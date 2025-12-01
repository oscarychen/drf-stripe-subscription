from unittest.mock import patch, MagicMock
from django.test import override_settings
from drf_stripe.models import get_drf_stripe_user_model as get_user_model
from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.customer_portal import stripe_api_create_billing_portal_session
from drf_stripe.settings import drf_stripe_settings
from .base import BaseTest


class TestCustomerPortalSettings(BaseTest):
    """Test for customer portal return URL configuration."""

    @patch('drf_stripe.stripe_api.customer_portal.stripe.billing_portal.Session.create')
    def test_default_customer_portal_return_url(self, mock_session_create):
        """Test that the default customer portal return URL is used."""
        # Mock the Stripe API response
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/test123"
        mock_session_create.return_value = mock_session
        
        # Create a test user and stripe user
        user = get_user_model().objects.create(username="test_user", email="test@example.com")
        StripeUser.objects.create(user_id=user.id, customer_id="cus_test123")
        
        # Call the function
        session = stripe_api_create_billing_portal_session(user.id)
        
        # Verify the session was created with the correct return URL
        mock_session_create.assert_called_once()
        call_kwargs = mock_session_create.call_args[1]
        self.assertIn('return_url', call_kwargs)
        # Default FRONT_END_BASE_URL is http://localhost:3000
        # Default CUSTOMER_PORTAL_RETURN_URL_PATH is manage-subscription
        self.assertEqual(call_kwargs['return_url'], 'http://localhost:3000/manage-subscription/')

    @patch('drf_stripe.stripe_api.customer_portal.stripe.billing_portal.Session.create')
    def test_custom_customer_portal_return_url(self, mock_session_create):
        """Test that a custom customer portal return URL can be configured."""
        # Mock the Stripe API response
        mock_session = MagicMock()
        mock_session.url = "https://billing.stripe.com/session/test123"
        mock_session_create.return_value = mock_session
        
        # Create a test user and stripe user
        user = get_user_model().objects.create(username="test_user2", email="test2@example.com")
        StripeUser.objects.create(user_id=user.id, customer_id="cus_test456")
        
        # Override the setting to use a custom return URL path
        with override_settings(DRF_STRIPE={
            'FRONT_END_BASE_URL': 'https://example.com',
            'CUSTOMER_PORTAL_RETURN_URL_PATH': 'billing/portal',
        }):
            # Reload settings to pick up the override
            drf_stripe_settings.reload()
            
            # Call the function
            session = stripe_api_create_billing_portal_session(user.id)
            
            # Verify the session was created with the custom return URL
            mock_session_create.assert_called_once()
            call_kwargs = mock_session_create.call_args[1]
            self.assertIn('return_url', call_kwargs)
            self.assertEqual(call_kwargs['return_url'], 'https://example.com/billing/portal/')
