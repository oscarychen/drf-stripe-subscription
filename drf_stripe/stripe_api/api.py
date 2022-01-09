import stripe

from ..settings import drf_stripe_settings

stripe.api_key = drf_stripe_settings.STRIPE_API_SECRET

stripe_api = stripe
