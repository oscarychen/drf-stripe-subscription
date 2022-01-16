from drf_stripe.models import Subscription
from drf_stripe.stripe_api.subscriptions import stripe_api_update_subscriptions
from ..base import BaseTest


class TestSubscription(BaseTest):
    def setUp(self) -> None:
        self.setup_user_customer()
        self.setup_product_prices()

    def test_update_subscriptions(self):
        """
        Test retrieving list of subscription from Stripe and update database.
        """

        response = self._load_test_data("v1/api_subscription_list.json")

        stripe_api_update_subscriptions(test_data=response)

        subscription = Subscription.objects.get(subscription_id="sub_0001")
        self.assertEqual(subscription.status, "trialing")
        self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")
        sub_items = subscription.items.all()
        self.assertEqual(len(sub_items), 1)
        sub_item = sub_items.first()
        self.assertEqual(sub_item.price.price_id, "price_1KHkCLL14ex1CGCipzcBdnOp")
