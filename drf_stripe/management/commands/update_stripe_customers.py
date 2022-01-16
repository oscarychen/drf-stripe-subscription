from django.core.management.base import BaseCommand

from drf_stripe.stripe_api.customers import stripe_api_update_customers


class Command(BaseCommand):
    help = "Import Stripe Customer objects from Stripe"

    def add_arguments(self, parser):
        parser.add_argument("-l", "--limit", type=int, help="Limit", default=100)
        parser.add_argument("-s", "--starting_after", type=str, help="Starting after customer id", default=None)

    def handle(self, *args, **kwargs):
        stripe_api_update_customers(limit=kwargs.get('limit'), starting_after=kwargs.get('starting_after'))
