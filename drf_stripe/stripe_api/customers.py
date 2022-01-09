from stripe.error import InvalidRequestError

from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.api import stripe_api as stripe


def get_or_create_stripe_user(user_instance, verify: bool = False) -> StripeUser:
    """
    Get or create a StripeUser given a User instance.

    :param user_instance: Django User instance.
    :param bool verify: Defaults to False. If set to True, checks with Stripe to make sure a Customer exists
        and matches our StripeUser instance.
    """

    # StripeUser already exist
    if hasattr(user_instance, "stripe_user"):
        stripe_user = user_instance.stripe_user
        if verify is True:
            try:
                customer = stripe.Customer.retrieve(stripe_user.stripe_id, expand=['subscriptions'])
                # TODO: sync subscriptions?
            except InvalidRequestError:
                stripe_user, customer = _stripe_api_create_customer(user_instance)

    else:  # StripeUser does not exist
        stripe_user = _stripe_api_create_customer(user_instance)
    return stripe_user


def _stripe_api_create_customer(user_instance) -> StripeUser:
    """
    Using Stripe API to creates a stripe Customer;
    create and attach the corresponding StripeUser to a given User instance.
    Avoid using this function directly, call get_or_create_stripe_user() instead.

    :param user_instance: Django User instance.
    """
    customer = stripe.Customer.create(email=user_instance.email)
    stripe_user, _ = StripeUser.objects.update_or_create(user=user_instance, defaults={"stripe_id": customer.id})
    return stripe_user
