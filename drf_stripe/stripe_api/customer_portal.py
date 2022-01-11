from .api import stripe_api as stripe
from .customers import get_or_create_stripe_user
from ..settings import drf_stripe_settings


def stripe_api_create_billing_portal_session(user_id):
    """
    Creates a Stripe Customer Portal Session.

    :param str user_id: Django User id
    """
    stripe_user = get_or_create_stripe_user(user_id=user_id)

    session = stripe.billing_portal.Session.create(
        customer=stripe_user.customer_id,
        return_url=f"{drf_stripe_settings.FRONT_END_BASE_URL}/manage-subscription/"
    )

    return session
