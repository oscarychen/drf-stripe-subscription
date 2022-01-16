from django.contrib.auth import get_user_model

from drf_stripe.models import StripeUser
from drf_stripe.stripe_api.customers import stripe_api_update_customers
from ..base import BaseTest


class TestCustomer(BaseTest):
    def setUp(self) -> None:
        self.setup_user_customer()
        self.setup_product_prices()

    def test_update_customers(self):
        """
        Test retrieving list of customers from Stripe and creation of Django User and StripeUser instances.
        """
        
        response = self._load_test_data("v1/api_customer_list_2_items.json")

        stripe_api_update_customers(test_data=response)

        user_1 = get_user_model().objects.get(email="tester1@example.com")
        stripe_user_1 = StripeUser.objects.get(user=user_1)
        self.assertEqual(stripe_user_1.customer_id, "cus_tester")

        user_2 = get_user_model().objects.get(email="tester2@example.com")
        stripe_user_2 = StripeUser.objects.get(user=user_2)
        self.assertEqual(stripe_user_2.customer_id, "cus_tester2")

        user_3 = get_user_model().objects.get(email="tester3@example.com")
        stripe_user_3 = StripeUser.objects.get(user=user_3)
        self.assertEqual(stripe_user_3.customer_id, "cus_tester3")
