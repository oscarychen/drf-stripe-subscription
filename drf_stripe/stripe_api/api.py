import stripe

from ..settings import drf_stripe_settings

stripe.api_key = drf_stripe_settings.STRIPE_API_SECRET
stripe.api_version = "2020-08-27"

stripe_api = stripe
