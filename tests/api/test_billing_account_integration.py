"""Tests for billing account integration with pull_stripe command."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from drf_stripe.models import Subscription, StripeUser
from drf_stripe.settings import drf_stripe_settings
from drf_stripe.stripe_api.customers import stripe_api_update_customers
from drf_stripe.stripe_api.subscriptions import stripe_api_update_subscriptions
from tests.base import BaseTest
from tests.models import CustomBilling


class TestBillingAccountIntegration(BaseTest):
    """Test that pull_stripe updates billing account fields correctly."""

    def setUp(self) -> None:
        self.setup_product_prices()
        # Create a user and a custom billing account with that user as manager
        self.user = get_user_model().objects.create(
            username="tester",
            email="tester1@example.com",
            password="12345"
        )
        self.custom_billing = CustomBilling.objects.create(
            name="Test CustomBilling",
            manager_user=self.user
        )
        # Create StripeUser for the test user
        self.stripe_user = StripeUser.objects.create(
            user_id=self.user.id,
            customer_id="cus_tester"
        )

    def get_billing_settings(self):
        """Return DRF_STRIPE settings with BILLING_ACCOUNT_MODEL configured."""
        settings_copy = dict(drf_stripe_settings.user_settings)
        settings_copy['BILLING_ACCOUNT_MODEL'] = 'tests.CustomBilling'
        return settings_copy

    def test_update_subscriptions_links_to_billing_account_by_manager_user(self):
        """
        Test that stripe_api_update_subscriptions links subscription to billing account
        when BILLING_ACCOUNT_MODEL is configured and custom billing has manager_user.
        """
        with override_settings(DRF_STRIPE=self.get_billing_settings()):
            drf_stripe_settings.reload()

            response = self._load_test_data("v1/api_subscription_list.json")
            # Only use the first subscription (for cus_tester)
            response['data'] = [response['data'][0]]

            stripe_api_update_subscriptions(test_data=response)

            # Check that subscription was created and linked to billing account
            subscription = Subscription.objects.get(subscription_id="sub_0001")
            self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")

            # Check that billing account content type and object id are set
            custom_billing_ct = ContentType.objects.get_for_model(CustomBilling)
            self.assertEqual(subscription.billing_account_content_type, custom_billing_ct)
            self.assertEqual(subscription.billing_account_object_id, self.custom_billing.pk)

            # Check that billing account fields are updated
            self.custom_billing.refresh_from_db()
            self.assertEqual(self.custom_billing.stripe_customer_id, "cus_tester")
            self.assertEqual(self.custom_billing.stripe_subscription_id, "sub_0001")

            drf_stripe_settings.reload()

    def test_update_subscriptions_links_by_stripe_customer_id(self):
        """
        Test that stripe_api_update_subscriptions finds billing account by stripe_customer_id
        when the billing account already has it set.
        """
        # Set the stripe_customer_id on the custom billing first
        self.custom_billing.stripe_customer_id = "cus_tester"
        self.custom_billing.save()

        with override_settings(DRF_STRIPE=self.get_billing_settings()):
            drf_stripe_settings.reload()

            response = self._load_test_data("v1/api_subscription_list.json")
            response['data'] = [response['data'][0]]

            stripe_api_update_subscriptions(test_data=response)

            # Check that subscription was linked to billing account
            subscription = Subscription.objects.get(subscription_id="sub_0001")
            custom_billing_ct = ContentType.objects.get_for_model(CustomBilling)
            self.assertEqual(subscription.billing_account_content_type, custom_billing_ct)
            self.assertEqual(subscription.billing_account_object_id, self.custom_billing.pk)

            # Check that stripe_subscription_id is updated
            self.custom_billing.refresh_from_db()
            self.assertEqual(self.custom_billing.stripe_subscription_id, "sub_0001")

            drf_stripe_settings.reload()

    def test_update_customers_updates_billing_account_stripe_customer_id(self):
        """
        Test that stripe_api_update_customers updates the billing account's stripe_customer_id
        when BILLING_ACCOUNT_MODEL is configured.
        """
        # Reset the stripe_customer_id on custom billing
        self.custom_billing.stripe_customer_id = None
        self.custom_billing.save()

        with override_settings(DRF_STRIPE=self.get_billing_settings()):
            drf_stripe_settings.reload()

            response = self._load_test_data("v1/api_customer_list_2_items.json")
            # Only use the first customer (tester1@example.com)
            response['data'] = [response['data'][0]]

            stripe_api_update_customers(test_data=response)

            # Check that billing account stripe_customer_id is updated
            self.custom_billing.refresh_from_db()
            self.assertEqual(self.custom_billing.stripe_customer_id, "cus_tester")

            drf_stripe_settings.reload()

    def test_update_subscriptions_without_billing_model_works_as_before(self):
        """
        Test that stripe_api_update_subscriptions works as before when
        BILLING_ACCOUNT_MODEL is not configured.
        """
        response = self._load_test_data("v1/api_subscription_list.json")
        response['data'] = [response['data'][0]]

        stripe_api_update_subscriptions(test_data=response)

        # Check that subscription was created
        subscription = Subscription.objects.get(subscription_id="sub_0001")
        self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")

        # Check that billing account fields are NOT set (legacy behavior)
        self.assertIsNone(subscription.billing_account_content_type)
        self.assertIsNone(subscription.billing_account_object_id)

        # CustomBilling should not be updated
        self.custom_billing.refresh_from_db()
        self.assertIsNone(self.custom_billing.stripe_customer_id)
        self.assertIsNone(self.custom_billing.stripe_subscription_id)
