from django.core.management.base import BaseCommand

from drf_stripe.stripe_api.products import stripe_api_update_products_prices


class Command(BaseCommand):
    help = "Import Service/Feature types from Stripe"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        stripe_api_update_products_prices()
