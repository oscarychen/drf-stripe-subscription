from django.core.management.base import BaseCommand
from django.apps import apps as django_apps
from django.contrib.contenttypes.models import ContentType
from drf_stripe.models import StripeUser, Subscription
from drf_stripe.settings import drf_stripe_settings


class Command(BaseCommand):
    """Create BillingAccount entries for existing StripeUser records and attach existing Subscriptions. Only runs if BILLING_ACCOUNT_MODEL is configured."""
    help = "Create BillingAccount entries for existing StripeUser records and attach existing Subscriptions. Only runs if BILLING_ACCOUNT_MODEL is configured."

    def handle(self, *args, **options):
        BillingModelPath = drf_stripe_settings.BILLING_ACCOUNT_MODEL
        if not BillingModelPath:
            self.stdout.write(self.style.WARNING("DRF_STRIPE.BILLING_ACCOUNT_MODEL not configured. Nothing to migrate."))
            return
        try:
            app_label, model_name = BillingModelPath.split('.', 1)
            BillingModel = django_apps.get_model(app_label, model_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cannot resolve BillingModel '{BillingModelPath}': {e}"))
            return

        users = StripeUser.objects.all()
        for su in users:
            user = su.user
            try:
                ct = ContentType.objects.get_for_model(user.__class__)
                # If BillingModel uses Generic relation (most common when based on AbstractBillingAccount),
                # create using content_type/object_id
                billing_account, created = BillingModel.objects.get_or_create(
                    content_type=ct,
                    object_id=user.pk,
                    defaults={"stripe_customer_id": su.customer_id}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Created BillingAccount {billing_account.pk} for user {user.pk}"))
                else:
                    self.stdout.write(f"Existing BillingAccount {billing_account.pk} for user {user.pk}")

                # Move subscriptions that link to stripe_user to use billing account's generic reference fields if applicable
                for sub in Subscription.objects.filter(stripe_user=su):
                    if hasattr(BillingModel, 'content_type'):
                        sub.billing_account_content_type = ContentType.objects.get_for_model(BillingModel)
                        sub.billing_account_object_id = billing_account.pk
                        sub.save(update_fields=["billing_account_content_type", "billing_account_object_id"])
                        self.stdout.write(f"Moved Subscription {sub.subscription_id} to BillingAccount {billing_account.pk}")
                    else:
                        self.stdout.write(self.style.WARNING(f"BillingModel {BillingModelPath} does not use content_type/object_id; manual migration required for subscription {sub.subscription_id}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed migrating user {user.pk}: {e}"))
