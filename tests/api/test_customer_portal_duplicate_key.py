from unittest.mock import patch, MagicMock
from drf_stripe.models import get_drf_stripe_user_model as get_user_model
from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.customers import get_or_create_stripe_user
from ..base import BaseTest


class TestCustomerPortalDuplicateKey(BaseTest):
    """Test for duplicate key issue when accessing customer portal with multiple subscriptions."""

    @patch('drf_stripe.stripe_api.customers._stripe_api_get_or_create_customer_from_email')
    def test_get_or_create_stripe_user_multiple_calls(self, mock_stripe_customer):
        """
        Test that calling get_or_create_stripe_user multiple times for the same user
        does not cause a duplicate key error.
        
        This simulates the scenario where a user has multiple subscriptions and
        accesses the customer portal, which should work without errors.
        """
        # Mock the Stripe API response
        mock_customer = MagicMock()
        mock_customer.id = "cus_test123"
        mock_stripe_customer.return_value = mock_customer
        
        # Create a test user
        user = get_user_model().objects.create(username="test_user", email="test@example.com")
        
        # First call to get_or_create_stripe_user (simulating first subscription)
        stripe_user1 = get_or_create_stripe_user(user_id=user.id)
        self.assertIsNotNone(stripe_user1)
        self.assertIsNotNone(stripe_user1.customer_id)
        
        # Store the customer_id from first call
        first_customer_id = stripe_user1.customer_id
        
        # Second call to get_or_create_stripe_user (simulating second subscription or customer portal access)
        # This should NOT fail with a duplicate key error
        stripe_user2 = get_or_create_stripe_user(user_id=user.id)
        self.assertIsNotNone(stripe_user2)
        self.assertEqual(stripe_user2.customer_id, first_customer_id)
        
        # Verify that both calls return the same StripeUser instance
        self.assertEqual(stripe_user1.user_id, stripe_user2.user_id)
        
        # Verify there's only one StripeUser for this user
        stripe_user_count = StripeUser.objects.filter(user_id=user.id).count()
        self.assertEqual(stripe_user_count, 1)

    def test_get_or_create_stripe_user_with_existing_stripe_user(self):
        """
        Test that get_or_create_stripe_user works correctly when a StripeUser
        already exists for the user.
        """
        # Create a test user and StripeUser directly
        user = get_user_model().objects.create(username="existing_user", email="existing@example.com")
        existing_stripe_user = StripeUser.objects.create(user_id=user.id, customer_id="cus_existing123")
        
        # Call get_or_create_stripe_user
        stripe_user = get_or_create_stripe_user(user_id=user.id)
        
        # Should return the existing StripeUser
        self.assertEqual(stripe_user.user_id, existing_stripe_user.user_id)
        self.assertEqual(stripe_user.customer_id, existing_stripe_user.customer_id)
        
        # Verify there's still only one StripeUser
        stripe_user_count = StripeUser.objects.filter(user_id=user.id).count()
        self.assertEqual(stripe_user_count, 1)
