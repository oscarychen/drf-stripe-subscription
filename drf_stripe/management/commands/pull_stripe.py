from django.core.management import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Pull data from Stripe and update database."

    def handle(self, *args, **kwargs):
        call_command("update_stripe_products")
        call_command("update_stripe_customers")
        call_command("update_stripe_subscriptions")
