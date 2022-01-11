from typing import overload

from django.contrib.auth import get_user_model

from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.api import stripe_api as stripe


@overload
def get_or_create_stripe_user(user_instance) -> StripeUser:
    ...


@overload
def get_or_create_stripe_user(user_id, user_email) -> StripeUser:
    ...


@overload
def get_or_create_stripe_user(user_id) -> StripeUser:
    ...


def get_or_create_stripe_user(**kwargs) -> StripeUser:
    """
    Get or create a StripeUser given a User instance, or given user id and user email.

    :key user_instance: Django user instance.
    :key user_id: Django User id.
    :key user_email: user email address
    """
    user_instance = kwargs.get("user_instance")
    user_id = kwargs.get("user_id")
    user_email = kwargs.get("user_email")

    if user_instance and isinstance(user_instance, get_user_model()):
        return _get_or_create_stripe_user_from_user_instance(user_instance)
    elif user_id and user_email and isinstance(user_id, str):
        return _get_or_create_stripe_user_from_user_id_email(user_id, user_email)
    elif user_id is not None:
        return _get_or_create_stripe_user_from_user_id(user_id)
    else:
        raise TypeError("Unknown keyword arguments!")


def _get_or_create_stripe_user_from_user_instance(user_instance):
    """
    Return a StripeUser instance given a Django User instance.

    :param user_instance: Django User instance.
    """
    return _get_or_create_stripe_user_from_user_id_email(user_instance.id, user_instance.email)


def _get_or_create_stripe_user_from_user_id(user_id):
    """
    Return a StripeUser instance given user_id.

    :param user_id: user id
    """
    user = get_user_model().objects.get(id=user_id)

    return _get_or_create_stripe_user_from_user_id_email(user.id, user.email)


def _get_or_create_stripe_user_from_user_id_email(user_id, user_email: str):
    """
    Return a StripeUser instance given user_id and user_email.

    :param user_id: user id
    :param string user_email: user email address
    """
    stripe_user, created = StripeUser.objects.get_or_create(user_id=user_id)

    if created:
        customer = stripe.Customer.create(email=user_email)
        stripe_user.customer_id = customer.id
        stripe_user.save()

    return stripe_user
