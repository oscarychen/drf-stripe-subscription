from django.contrib.auth import get_user_model
from drf_stripe.models import Subscription, StripeUser
from drf_stripe.stripe_api.subscriptions import stripe_api_update_subscriptions
from ..base import BaseTest

from unittest.mock import patch
from drf_stripe.settings import drf_stripe_settings
from django.test import override_settings


class TestSubscription(BaseTest):
    def setUp(self) -> None:
        self.setup_user_customer()
        self.setup_product_prices()

    @patch('stripe.Customer.retrieve')
    def test_update_subscriptions(self, mocked_retrieve_fn):
        """
        Test retrieving list of subscription from Stripe and update database.
        """

        response = self._load_test_data("v1/api_subscription_list.json")
        mocked_retrieve_fn.return_value = {
            "email": "tester2@example.com",
            "id": "cus_tester2",
        }

        stripe_api_update_subscriptions(test_data=response)

        subscription = Subscription.objects.get(subscription_id="sub_0001")
        self.assertEqual(subscription.status, "trialing")
        self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")
        sub_items = subscription.items.all()
        self.assertEqual(len(sub_items), 1)
        sub_item = sub_items.first()
        self.assertEqual(sub_item.price.price_id, "price_1KHkCLL14ex1CGCipzcBdnOp")

        subscription2 = Subscription.objects.get(subscription_id="sub_0002")
        self.assertEqual(subscription2.status, "trialing")
        self.assertEqual(subscription2.stripe_user.customer_id, "cus_tester2")
        sub2_items = subscription2.items.all()
        self.assertEqual(len(sub2_items), 1)
        sub2_item = sub2_items.first()
        self.assertEqual(sub2_item.price.price_id, "price_1KHkCLL14ex1CGCipzcBdnOp")

        user_2 = get_user_model().objects.filter(email="tester2@example.com").first()
        self.assertIsNotNone(user_2)
        stripe_user_2 = StripeUser.objects.filter(customer_id="cus_tester2").first()
        self.assertIsNotNone(stripe_user_2)

    @patch('stripe.Customer.retrieve')
    def test_update_subscriptions_without_creating_django_users(self, mocked_retrieve_fn):
        """
        Test retrieving list of subscription from Stripe and update database without creating django users if they don't already exist.
        """
        drf_stripe_copy = drf_stripe_settings.user_settings
        drf_stripe_copy['USER_CREATE_DEFAULTS_ATTRIBUTE_MAP'] = None
        with override_settings(DRF_STRIPE=drf_stripe_copy):
            response = self._load_test_data("v1/api_subscription_list.json")

            mocked_retrieve_fn.return_value = {
                "email": "tester2@example.com",
                "id": "cus_tester2",
            }

            stripe_api_update_subscriptions(test_data=response, ignore_new_user_creation_errors=True)

        subscription = Subscription.objects.get(subscription_id="sub_0001")
        self.assertEqual(subscription.status, "trialing")
        self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")
        sub_items = subscription.items.all()
        self.assertEqual(len(sub_items), 1)
        sub_item = sub_items.first()
        self.assertEqual(sub_item.price.price_id, "price_1KHkCLL14ex1CGCipzcBdnOp")

        subscription2 = Subscription.objects.filter(subscription_id="sub_0002").first()
        self.assertIsNone(subscription2)

        user_2 = get_user_model().objects.filter(email="tester2@example.com").first()
        self.assertIsNone(user_2)
        stripe_user_2 = StripeUser.objects.filter(customer_id="cus_tester2").first()
        self.assertIsNone(stripe_user_2)
