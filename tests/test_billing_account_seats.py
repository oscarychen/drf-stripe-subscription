"""
Test that the DEFAULT_MAX_SUBSCRIPTION_QUANTITY setting works correctly for subscription quantities.
"""
from django.test import TestCase, override_settings
from drf_stripe.settings import drf_stripe_settings


class TestDefaultMaxSubscriptionQuantity(TestCase):
    """Test DEFAULT_MAX_SUBSCRIPTION_QUANTITY setting behavior."""

    def test_default_subscription_quantity_setting_exists(self):
        """Verify the DEFAULT_MAX_SUBSCRIPTION_QUANTITY setting is accessible."""
        self.assertEqual(drf_stripe_settings.DEFAULT_MAX_SUBSCRIPTION_QUANTITY, 1)

    @override_settings(DRF_STRIPE={"DEFAULT_MAX_SUBSCRIPTION_QUANTITY": 5})
    def test_default_subscription_quantity_can_be_overridden(self):
        """Verify the DEFAULT_MAX_SUBSCRIPTION_QUANTITY setting can be overridden."""
        # Need to reload settings after override
        drf_stripe_settings.reload()
        self.assertEqual(drf_stripe_settings.DEFAULT_MAX_SUBSCRIPTION_QUANTITY, 5)
        # Reload again to restore default
        drf_stripe_settings.reload()
