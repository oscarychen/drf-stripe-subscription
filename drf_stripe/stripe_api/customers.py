from typing import overload

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import atomic

from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.api import stripe_api as stripe
from drf_stripe.stripe_models.customer import StripeCustomers, StripeCustomer


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

    :param str customer_id: Stripe customer id
    """

    try:
        user = get_user_model().objects.get(stripe_user__customer_id=customer_id)

    except ObjectDoesNotExist:
        customer_response = stripe.Customer.retrieve(customer_id)
        customer = StripeCustomer(**customer_response)
        user, created = get_user_model().objects.get_or_create(
            email=customer.email,
            defaults={"username": customer.email}
        )
        if created:
            print(f"Created new User with customer_id {customer_id}")

    return _get_or_create_stripe_user_from_user_id_email(user.id, user.email)


def _get_or_create_stripe_user_from_user_id_email(user_id, user_email: str):
    """
    Return a StripeUser instance given user_id and user_email.

    :param user_id: user id
    :param str user_email: user email address
    """
    stripe_user, created = StripeUser.objects.get_or_create(user_id=user_id)

    if created:
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
    Retrieve list of Stripe customer objects, and create Django User and StripeUser instances.

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

    user_creation_count = 0
    stripe_user_creation_count = 0

    for customer in stripe_customers:
        # Stripe customer can have null as email
        if customer.email is not None:
            user, user_created = get_user_model().objects.get_or_create(
                email=customer.email,
                defaults={"username": customer.email}
            )
            stripe_user, stripe_user_created = StripeUser.objects.get_or_create(user=user,
                                                                                defaults={"customer_id": customer.id})
            print(f"Updated Stripe Customer {customer.id}")

    if user_created is True:
        user_creation_count += 1
    if stripe_user_created is True:
        stripe_user_creation_count += 1

    print(f"{user_creation_count} user(s) created, {stripe_user_creation_count} user(s) linked to Stripe customers.")
