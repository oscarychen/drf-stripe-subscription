from datetime import timedelta, datetime
from functools import reduce
from typing import overload, List, Union
from urllib.parse import urljoin

from drf_stripe.models import get_drf_stripe_user_model as get_user_model
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
    :key int quantity: Defaults to 1.
    :key datetime trial_end: start the subscription with a trial.
    :key list line_items: Used when multiple price + quantity params need to be used. Defaults to None.
        If specified, supersedes price_id and quantity arguments.
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
    :param int quantity: Defaults to 1.
    :param datetime trial_end: start the subscription with a trial.
    :param list line_items: Used when multiple price + quantity params need to be used. Defaults to None.
        If specified, supersedes price_id and quantity arguments.
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


def _make_stripe_checkout_params(
        customer_id: str, price_id: str = None, quantity: int = 1, line_items: List[dict] = None,
        trial_end: Union[str, datetime, None] = 'auto', discounts: List[dict] = None,
        payment_method_types: List[str] = None, checkout_mode: str = drf_stripe_settings.DEFAULT_CHECKOUT_MODE
):
    if price_id is None and line_items is None:
        raise ValueError("Invalid arguments: must provide either a 'price_id' or 'line_items'.")
    elif price_id is not None and line_items is not None:
        raise ValueError("Invalid arguments: 'price_id' and 'line_items' should be used at the same time.")

    if price_id is not None:
        line_items = [{'price': price_id, 'quantity': quantity}]

    if payment_method_types is None:
        payment_method_types = drf_stripe_settings.DEFAULT_PAYMENT_METHOD_TYPES

    success_url = reduce(urljoin, (drf_stripe_settings.FRONT_END_BASE_URL,
                                   drf_stripe_settings.CHECKOUT_SUCCESS_URL_PATH,
                                   "?session={CHECKOUT_SESSION_ID}"))

    cancel_url = reduce(urljoin, (drf_stripe_settings.FRONT_END_BASE_URL,
                                  drf_stripe_settings.CHECKOUT_CANCEL_URL_PATH))

    params = {
        "customer": customer_id,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "payment_method_types": payment_method_types,
        "mode": checkout_mode,
        "line_items": line_items,
        "subscription_data": {
            "trial_end": _make_trial_end_timestamp(trial_end=trial_end)
        }
    }

    allow_promotion_codes = drf_stripe_settings.ALLOW_PROMOTION_CODES

    if allow_promotion_codes:
        params.update({"allow_promotion_codes": allow_promotion_codes})
    else:
        params.update({"discounts": discounts if discounts else drf_stripe_settings.DEFAULT_DISCOUNTS})

    return params


def _make_trial_end_timestamp(trial_end: Union[str, None, datetime] = 'auto'):
    """
    Returns a new trial_end time to be used for setting up new Stripe Subscription.
    Stripe requires new Subscription trial_end to be at least 48 hours in the future.

    :param trial_end: Explicitly set trial end datetime.
        Defaults to 'auto', which will return a calculated trial_end based on NEW_USER_FREE_TRIAL_DAYS setting.
        If set to less than 48 hours from now, will return the minimum required trial_end acceptable to Stripe API.
        If set to None, no trial, returns None.
    """
    if trial_end is None:
        return

    if trial_end == 'auto':
        if drf_stripe_settings.NEW_USER_FREE_TRIAL_DAYS is None:
            return
        else:
            trial_end = timezone.now() + timezone.timedelta(days=drf_stripe_settings.NEW_USER_FREE_TRIAL_DAYS + 1)

    min_trial_end = timezone.now() + timedelta(hours=49)
    if trial_end < min_trial_end:
        trial_end = min_trial_end

    return int(trial_end.replace(microsecond=0).timestamp())
