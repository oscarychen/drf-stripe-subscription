from drf_stripe.models import Subscription, SubscriptionItem
from drf_stripe.stripe_webhooks.handler import handle_webhook_event
from ..base import BaseTest


class TestWebhookSubscriptionEvents(BaseTest):

    def setUp(self) -> None:
        self.setup_product_prices()
        self.setup_user_customer()

    def create_subscription(self):
        # create subscription
        event = self._load_test_data("2020-08-27/webhook_subscription_created.json")
        handle_webhook_event(event)

    def test_event_handler_subscription_created(self):
        """Mock customer subscription creation event"""

        self.create_subscription()

        # check subscription instance is created
        subscription = Subscription.objects.get(subscription_id="sub_1KHlYHL14ex1CGCiIBo8Xk5p")
        self.assertEqual(subscription.stripe_user.customer_id, "cus_tester")

        # check subscription item instance is created
        sub_item = SubscriptionItem.objects.get(sub_item_id="si_KxgwlJyHxmgJKx")
        self.assertEqual(sub_item.subscription.subscription_id, subscription.subscription_id)
        self.assertEqual(sub_item.price.price_id, "price_1KHkCLL14ex1CGCipzcBdnOp")
        self.assertEqual(sub_item.price.product.product_id, "prod_KxfXRXOd7dnLbz")

    def test_event_handler_subscription_updated_price_plan_change(self):
        """Mock customer subscription being modified event"""

        self.create_subscription()

        event = self._load_test_data("2020-08-27/webhook_subscription_updated_billing_frequency.json")
        handle_webhook_event(event)

        # check subscription is updated with new price
        subscription = Subscription.objects.get(subscription_id="sub_1KHlYHL14ex1CGCiIBo8Xk5p")

        # check SubscriptionItem with previous price is deleted
        old = SubscriptionItem.objects.filter(price_id="price_1KHkCLL14ex1CGCipzcBdnOp")
        self.assertEqual(len(old), 0)

        # check SubscriptionItem with new price is created
        sub_item = SubscriptionItem.objects.get(price_id="price_1KHkCLL14ex1CGCieIBu8V2e")
        self.assertEqual(sub_item.subscription.subscription_id, subscription.subscription_id)

    def test_event_handler_subscription_updated_coupon_added(self):
        self.create_subscription()

        event = self._load_test_data("2020-08-27/webhook_subscription_updated_apply_coupon.json")
        handle_webhook_event(event)

        # TODO: coupon not implemented yet

    def test_event_handler_subscription_updated_cancel_at_period_end(self):
        """Mock customer subscription cancelling at end of period"""
        self.create_subscription()
        event = self._load_test_data("2020-08-27/webhook_subscription_updated_cancel_at_period_end.json")
        handle_webhook_event(event)

        subscription = Subscription.objects.get(subscription_id="sub_1KHlYHL14ex1CGCiIBo8Xk5p")
        self.assertTrue(subscription.cancel_at_period_end)
        self.assertIsNotNone(subscription.cancel_at)

    def test_event_handler_subscription_updated_renewed(self):
        """Mock customer subscription renewed"""
        self.create_subscription()
        event = self._load_test_data("2020-08-27/webhook_subscription_updated_cancel_at_period_end.json")
        handle_webhook_event(event)
        event = self._load_test_data("2020-08-27/webhook_subscription_updated_renew_plan.json")
        handle_webhook_event(event)

        subscription = Subscription.objects.get(subscription_id="sub_1KHlYHL14ex1CGCiIBo8Xk5p")
        self.assertFalse(subscription.cancel_at_period_end)
        self.assertIsNone(subscription.cancel_at)
        self.assertIsNone(subscription.ended_at)

    def test_event_handler_subscription_updated_cancel_immediately(self):
        """Mock customer subscription cancelling immediately"""
        self.create_subscription()
        event = self._load_test_data("2020-08-27/webhook_subscription_updated_cancel_immediate.json")
        handle_webhook_event(event)

        subscription = Subscription.objects.get(subscription_id="sub_1KHlYHL14ex1CGCiIBo8Xk5p")
        self.assertIsNotNone(subscription.ended_at)
