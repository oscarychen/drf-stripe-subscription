from datetime import timedelta, datetime
from typing import overload

from django.contrib.auth import get_user_model
from django.utils import timezone

from drf_stripe.stripe_api.api import stripe_api as stripe
from ..settings import drf_stripe_settings


@overload
def stripe_api_create_checkout_session(customer_id: str, price_id: str, trial_end: datetime = None):
    ...


@overload
def stripe_api_create_checkout_session(user_instance, price_id: str, trial_end: datetime = None):
    ...


def stripe_api_create_checkout_session(**kwargs):
    """
    create a Stripe checkout session to start a subscription for user.
    You must provide either customer_id and price_id;
    or user_instance and price_id.
    Optionally provide a trial_end.

    :key user_instance: Django User instance.
    :key customer_id: Stripe customer id.
    :key str price_id: Stripe price id.
    :key datetime trial_end: start the subscription with a trial.
    """

    user_instance = kwargs.get("user_instance")
    customer_id = kwargs.get("customer_id")

    if user_instance and isinstance(user_instance, get_user_model()):
        return _stripe_api_create_checkout_session_for_user(**kwargs)
    elif customer_id and isinstance(customer_id, str):
        return _stripe_api_create_checkout_session_for_customer(**kwargs)
    else:
        raise TypeError("Unknown keyword arguments.")


def _stripe_api_create_checkout_session_for_customer(customer_id: str, **kwargs):
    """
    create a Stripe checkout session to start a subscription for user.

    :param customer_id: Stripe customer id.
    :param str price_id: Stripe price id.
    :param datetime trial_end: start the subscription with a trial.
    """
    stripe_checkout_params = _make_stripe_checkout_params(customer_id, **kwargs)

    return stripe.checkout.Session.create(**stripe_checkout_params)


def _stripe_api_create_checkout_session_for_user(user_instance, **kwargs):
    """
    create a Stripe checkout session to start a subscription for user.

    :param user_instance: Django User instance.
    :param str price_id: Stripe price id.
    :param bool trial_end: trial_end
    """

    return _stripe_api_create_checkout_session_for_customer(
        customer_id=user_instance.stripe_user.customer_id,
        **kwargs
    )


def _make_stripe_checkout_params(customer_id: str, price_id: str, quantity: int = 1, trial_end: datetime = None):
    return {
        "customer": customer_id,
        "success_url": f'{drf_stripe_settings.FRONT_END_BASE_URL}/payment/?session={{CHECKOUT_SESSION_ID}}/',
        "cancel_url": f'{drf_stripe_settings.FRONT_END_BASE_URL}/manage-subscription/',
        "payment_method_types": ['card'],
        "mode": 'subscription',
        "line_items": [
            {'price': price_id, 'quantity': quantity},
        ],
        "subscription_data": {
            "trial_end": int(_make_trial_end_datetime(trial_end=trial_end).timestamp())
        }
    }


def _make_trial_end_datetime(trial_end=None):
    """
    Returns a new trial_end time to be used for setting up new Stripe Subscription.
    Stripe requires new Subscription trial_end to be at least 48 hours in the future.
    Return None if less than 48 hours left to set up trialing with Stripe

    """
    if trial_end is None:
        trial_end = timezone.now() + timezone.timedelta(days=drf_stripe_settings.NEW_USER_FREE_TRIAL_DAYS)

    min_trial_end = timezone.now() + timedelta(hours=49)
    if trial_end < min_trial_end:
        trial_end = min_trial_end

    return trial_end.replace(microsecond=0)
