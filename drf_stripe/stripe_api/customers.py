from typing import overload

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from drf_stripe.models import get_drf_stripe_user_model as get_user_model
from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.api import stripe_api as stripe
from drf_stripe.stripe_models.customer import StripeCustomers, StripeCustomer
from ..settings import drf_stripe_settings


class CreatingNewUsersDisabledError(Exception):
    pass


def get_billing_model():
    """
    Returns the BillingAccount model class if BILLING_ACCOUNT_MODEL is configured, else None.
    """
    billing_model_path = drf_stripe_settings.BILLING_ACCOUNT_MODEL
    if not billing_model_path:
        return None
    try:
        app_label, model_name = billing_model_path.split('.', 1)
        return apps.get_model(app_label, model_name)
    except (ValueError, LookupError):
        try:
            return apps.get_model(billing_model_path)
        except LookupError:
            return None


def find_billing_account(billing_model, customer_id=None, user=None):
    """
    Find a billing account instance by stripe_customer_id or by manager_user.

    :param billing_model: The BillingAccount model class
    :param customer_id: Stripe customer id (optional)
    :param user: Django user instance (optional)
    :return: billing account instance or None
    """
    if billing_model is None:
        return None
    
    # First try by customer_id
    if customer_id:
        try:
            return billing_model.objects.filter(stripe_customer_id=customer_id).first()
        except Exception:
            pass
    
    # Then try by manager_user
    if user:
        try:
            return billing_model.objects.filter(manager_user=user).first()
        except Exception:
            pass
    
    return None


def update_billing_account_subscription(billing_model, billing_account, customer_id, subscription_id, subscription_defaults):
    """
    Update billing account stripe fields and add billing account link to subscription defaults.

    :param billing_model: The BillingAccount model class
    :param billing_account: The billing account instance
    :param customer_id: Stripe customer id
    :param subscription_id: Stripe subscription id
    :param subscription_defaults: Dictionary of subscription defaults to update
    :return: Updated subscription_defaults dictionary
    """
    if not billing_account:
        return subscription_defaults

    # Update billing account stripe fields
    update_fields = []
    if not billing_account.stripe_customer_id:
        billing_account.stripe_customer_id = customer_id
        update_fields.append("stripe_customer_id")
    if billing_account.stripe_subscription_id != subscription_id:
        billing_account.stripe_subscription_id = subscription_id
        update_fields.append("stripe_subscription_id")
    if update_fields:
        billing_account.save(update_fields=update_fields)

    # Link subscription to billing account
    subscription_defaults["billing_account_content_type"] = ContentType.objects.get_for_model(billing_model)
    subscription_defaults["billing_account_object_id"] = billing_account.pk

    return subscription_defaults


@overload
def get_or_create_stripe_user(user_instance) -> StripeUser:
    ...


@overload
def get_or_create_stripe_user(user_id, user_email) -> StripeUser:
    ...


@overload
def get_or_create_stripe_user(user_id) -> StripeUser:
    ...


@atomic()
def get_or_create_stripe_user(**kwargs) -> StripeUser:
    """
    Get or create a StripeUser given a User instance, or given user id and user email.

    :key user_instance: Django user instance.
    :key str user_id: Django User id.
    :key str user_email: user email address.
    :key str customer_id: Stripe customer id.
    """
    user_instance = kwargs.get("user_instance")
    user_id = kwargs.get("user_id")
    user_email = kwargs.get("user_email")
    customer_id = kwargs.get("customer_id")

    if user_instance and isinstance(user_instance, get_user_model()):
        return _get_or_create_stripe_user_from_user_instance(user_instance)
    elif user_id and user_email and isinstance(user_id, str):
        return _get_or_create_stripe_user_from_user_id_email(user_id, user_email)
    elif user_id is not None:
        return _get_or_create_stripe_user_from_user_id(user_id)
    elif customer_id is not None:
        return _get_or_create_stripe_user_from_customer_id(customer_id)
    else:
        raise TypeError("Unknown keyword arguments!")


def _get_or_create_stripe_user_from_user_instance(user_instance):
    """
    Returns a StripeUser instance given a Django User instance.

    :param user_instance: Django User instance.
    """
    return _get_or_create_stripe_user_from_user_id_email(user_instance.id, user_instance.email)


def _get_or_create_stripe_user_from_user_id(user_id):
    """
    Returns a StripeUser instance given user_id.

    :param str user_id: user id
    """
    user = get_user_model().objects.get(id=user_id)

    return _get_or_create_stripe_user_from_user_id_email(user.id, user.email)


def _get_or_create_stripe_user_from_customer_id(customer_id):
    """
    Returns a StripeUser instance given customer_id

    If there is no Django user connected to a StripeUser with the given customer_id then
    Stripe's customer API is called to get the customer's details (e.g. email address).
    Then if a Django user exists for that email address a StripeUser record will be created.
    If a Django user does not exist for that email address and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP
    is set then a Django user will be created along with a StripeUser record. If
    USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set then a CreatingNewUsersDisabledError will be raised.

    :param str customer_id: Stripe customer id
    """

    try:
        user = get_user_model().objects.get(stripe_user__customer_id=customer_id)

    except ObjectDoesNotExist:
        customer_response = stripe.Customer.retrieve(customer_id)
        customer = StripeCustomer(**customer_response)
        user, created = _get_or_create_django_user_if_configured(customer)
        if created:
            print(f"Created new User with customer_id {customer_id}")

    return _get_or_create_stripe_user_from_user_id_email(user.id, user.email, customer_id)


def _get_or_create_django_user_if_configured(customer: StripeCustomer):
    """
    If a Django user exists for the customer's email address it will be returned.
    If a Django user does not exist for the customer's email address and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP
    is set then a Django user will be created and returned.
    If USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set then a CreatingNewUsersDisabledError will be raised.

    :param customer: Stripe customer record
    """

    django_user_query_filters = {drf_stripe_settings.DJANGO_USER_EMAIL_FIELD: customer.email}
    django_user = get_user_model().objects.filter(
        **django_user_query_filters
    ).first()

    if django_user:
        return django_user, False

    if not drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP:
        raise CreatingNewUsersDisabledError(f"No Django user exists with Stripe customer id '{customer.id}'s email and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set so a Django user cannot be created.")

    defaults = {k: getattr(customer, v) for k, v in
                drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP.items()}
    defaults[drf_stripe_settings.DJANGO_USER_EMAIL_FIELD] = customer.email
    django_user = get_user_model().objects.create(
        **defaults
    )
    return django_user, True


def get_or_create_stripe_user_from_customer(customer: StripeCustomer) -> StripeUser:
    """
    Returns a StripeUser instance given customer, creating records if required.

    If a Django User record does not exist for the customer's email address and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is set
    then a new Django User record will be created with the email address and other values according to the USER_CREATE_DEFAULTS_ATTRIBUTE_MAP.
    If a Django User record does not exist for the customer's email address and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set then a CreatingNewUsersDisabledError will be thrown.

    :param customer: Stripe customer record
    """

    try:
        return StripeUser.objects.get(customer_id=customer.id)
    except ObjectDoesNotExist:

        django_user_query_filters = {drf_stripe_settings.DJANGO_USER_EMAIL_FIELD: customer.email}

        django_user = get_user_model().objects.filter(
            **django_user_query_filters
        ).first()

        if not django_user:
            if not drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP:
                raise CreatingNewUsersDisabledError(f"No Django user exists with Stripe customer id '{customer.id}'s email and USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set so a Django user cannot be created.")

            defaults = {k: getattr(customer, v) for k, v in
                            drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP.items()}
            defaults[drf_stripe_settings.DJANGO_USER_EMAIL_FIELD] = customer.email
            django_user = get_user_model().objects.create(
                **defaults
            )

            print(f"Created new Django User with email address for Stripe customer_id {customer.id}")

        stripe_user, stripe_user_created = StripeUser.objects.get_or_create(user_id=django_user.id, defaults={'customer_id': customer.id})
        if not stripe_user_created and stripe_user.customer_id:
            # there's an existing StripeUser record for the Django User with the given customer's email address, but it already has a different customer_id.
            # (if the existing customer_id matched this one then this function would have already returned)
            # As there is a OneToOne relationship between DjangoUser and StripeUser we cannot create another record here, and we shouldn't assume it is
            # safe to replace the reference to the existing Stripe Customer. So raise an error.
            raise ValueError(f"A StripeUser record already exists for Django user id '{django_user.id}' which references a different customer id - called with customer id '{customer.id}', existing db customer id: '{stripe_user.customer_id}'")

        return stripe_user


def _get_or_create_stripe_user_from_user_id_email(user_id, user_email: str, customer_id: str = None):
    """
    Return a StripeUser instance given user_id and user_email.

    :param user_id: user id
    :param str user_email: user email address
    :param str customer_id: Stripe customer id (optional)
    """
    defaults = {'customer_id': customer_id} if customer_id else {}
    stripe_user, created = StripeUser.objects.get_or_create(user_id=user_id, defaults=defaults)

    if created and not customer_id:
        customer = _stripe_api_get_or_create_customer_from_email(user_email)
        stripe_user.customer_id = customer.id
        stripe_user.save()

    return stripe_user


def _stripe_api_get_or_create_customer_from_email(user_email: str):
    """
    Get or create a Stripe customer by email address.
    Stripe allows creation of multiple customers with the same email address, therefore it is important that you use
    this method to create or retrieve a Stripe Customer instead of creating one by calling the Stripe API directly.

    :param str user_email: user email address
    """
    customers_response = stripe.Customer.list(email=user_email)
    stripe_customers = StripeCustomers(**customers_response).data

    if len(stripe_customers) > 0:
        customer = stripe_customers.pop()
    else:
        customer = stripe.Customer.create(email=user_email)

    return customer


@atomic
def stripe_api_update_customers(limit=100, starting_after=None, test_data=None):
    """
    Retrieve list of Stripe customer objects, create StripeUser instances and optionally Django User.
    If a Django user does not exist a Django User will be created if setting USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is set,
    otherwise the Customer will be skipped.

    When BILLING_ACCOUNT_MODEL is configured, this function will also update the billing account's
    stripe_customer_id field if the user is the manager_user of a billing account.

    Called from management command.

    :param int limit: Limit the number of customers to retrieve
    :param str starting_after: Stripe Customer id to start retrieval
    :param test_data: Stripe.Customer.list API response, used for testing
    """

    if limit < 0 or limit > 100:
        raise ValueError("Argument limit should be a positive integer no greater than 100.")

    if test_data is None:
        customers_response = stripe.Customer.list(limit=limit, starting_after=starting_after)
    else:
        customers_response = test_data

    stripe_customers = StripeCustomers(**customers_response).data

    billing_model = get_billing_model()

    user_creation_count = 0
    stripe_user_creation_count = 0

    for customer in stripe_customers:
        # Stripe customer can have null as email
        if customer.email is not None:
            query_filters = {drf_stripe_settings.DJANGO_USER_EMAIL_FIELD: customer.email}
            if drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP:
                defaults = {k: getattr(customer, v) for k, v in
                    drf_stripe_settings.USER_CREATE_DEFAULTS_ATTRIBUTE_MAP.items()}
                user, user_created = get_user_model().objects.get_or_create(
                    **query_filters,
                    defaults=defaults
                )
            else:
                user_created = False
                user = get_user_model().objects.filter(
                    **query_filters
                ).first()

            if user:
                stripe_user, stripe_user_created = StripeUser.objects.get_or_create(user=user,
                                                                                    defaults={"customer_id": customer.id})
                print(f"Updated Stripe Customer {customer.id}")

                # Update billing account if configured
                if billing_model:
                    billing_account = find_billing_account(billing_model, user=user)
                    if billing_account and not billing_account.stripe_customer_id:
                        billing_account.stripe_customer_id = customer.id
                        billing_account.save(update_fields=["stripe_customer_id"])
                        print(f"Updated billing account {billing_account.pk} with stripe_customer_id {customer.id}")

                if user_created is True:
                    user_creation_count += 1
                if stripe_user_created is True:
                    stripe_user_creation_count += 1
            else:
                print(f"Could not find Stripe Customer id '{customer.id}' in user model '{get_user_model()}' with '{drf_stripe_settings.DJANGO_USER_EMAIL_FIELD}' of '{customer.email}', USER_CREATE_DEFAULTS_ATTRIBUTE_MAP is not set so skipping Customer.")

    print(f"{user_creation_count} user(s) created, {stripe_user_creation_count} user(s) linked to Stripe customers.")
