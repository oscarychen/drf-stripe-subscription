from datetime import timedelta

from django.utils import timezone

from drf_stripe.stripe_api.api import stripe_api as stripe
from ..settings import drf_stripe_settings


def _make_stripe_checkout_params(customer_id: str, price_id: str, quantity: int = 1):
    return {
        "customer": customer_id,
        "success_url": f'{drf_stripe_settings.FRONT_END_BASE_URL}/payment/?session={{CHECKOUT_SESSION_ID}}/',
        "cancel_url": f'{drf_stripe_settings.FRONT_END_BASE_URL}/manage-subscription/',
        "payment_method_types": ['card'],
        "mode": 'subscription',
        "line_items": [
            {'price': price_id, 'quantity': quantity},
        ],
    }


def make_trial_end_timestamp(user_instance):
    """
    Returns a new trial_end time to be used for setting up new Stripe Subscription.
    Stripe requires new Subscription trial_end to be at least 48 hours in the future.
    Return None if less than 48 hours left to set up trialing with Stripe

    :param user_instance: Django User instance.
    """
    sub_exp = user_instance.date_joined + timezone.timedelta(days=drf_stripe_settings.NEW_USER_FREE_TRIAL_DAYS)
    min_trial_end = timezone.now() + timedelta(hours=49)
    if sub_exp is None:
        trial_end = min_trial_end
    elif sub_exp < min_trial_end:
        # not eligible to start trial subscription with Stripe
        return None
    else:
        trial_end = sub_exp
    return int(trial_end.replace(microsecond=0).timestamp())


def stripe_api_create_checkout_session(user_instance, price_id, trial=True):
    """
    create a Stripe checkout session to start a subscription for user.

    :param user_instance: Django User instance.
    :param str price_id: Stripe price id.
    :param bool trial: Defaults to True, start the subscription with a trial.
    """
    stripe_checkout_params = _make_stripe_checkout_params(user_instance.stripe_user.customer_id, price_id)

    if trial is True:
        trial_end_timestamp = make_trial_end_timestamp(user_instance)
        stripe_checkout_params['subscription_data'] = {'trial_end': trial_end_timestamp}

    checkout_session = stripe.checkout.Session.create(**stripe_checkout_params)
    return checkout_session
