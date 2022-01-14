from django.db.models import Q

from drf_stripe.models import Product, Price, ProductFeature
from drf_stripe.stripe_webhooks.handler import handle_webhook_event
from tests.base import BaseTest


class TestWebhookProductPriceEvents(BaseTest):

    def create_product_price(self):
        event = self._load_test_data("2020-08-27/webhook_product_created.json")
        handle_webhook_event(event)
        event = self._load_test_data("2020-08-27/webhook_price_created.json")
        handle_webhook_event(event)

    def test_event_handler_product_created(self):
        """
        Mock production and price creation events
        """
        self.create_product_price()

        # check product and price created
        product = Product.objects.get(description='Test Product ABC')
        price = Price.objects.get(product=product)
        self.assertEqual(price.price, 100)
        self.assertEqual(price.product, product)

        # check Product-to-Feature relations created
        ProductFeature.objects.get(product=product, feature__feature_id='A')
        ProductFeature.objects.get(product=product, feature__feature_id='B')
        ProductFeature.objects.get(product=product, feature__feature_id='C')

    def test_event_handler_price_update(self):
        """
        Mock price update events
        """
        self.create_product_price()

        # modify price
        event = self._load_test_data("2020-08-27/webhook_price_updated.json")
        handle_webhook_event(event)

        # check price modifications

        price = Price.objects.get(price_id="price_1KHkCLL14ex1CGCipzcBdnOp")

        self.assertEqual(price.price, 50)
        self.assertEqual(price.freq, "week_1")
        self.assertEqual(price.nickname, "Weekly subscription")
        self.assertEqual(price.product.product_id, "prod_KxfXRXOd7dnLbz")

    def test_event_handler_product_update(self):
        """Mock product update event"""
        self.create_product_price()

        # modify product
        product_mod = self._load_test_data("2020-08-27/webhook_product_updated.json")
        handle_webhook_event(product_mod)

        # check product modifications
        product = Product.objects.get(product_id='prod_KxfXRXOd7dnLbz')
        self.assertEqual(product.name, "Test Product ABD")
        self.assertEqual(product.description, "Test Product ABD")

        # check product is now associated with feature D
        ProductFeature.objects.get(product=product, feature__feature_id='D')
        ProductFeature.objects.get(product=product, feature__feature_id='A')
        ProductFeature.objects.get(product=product, feature__feature_id='B')

        # check product no longer associated with feature C
        prod_feature_qs = ProductFeature.objects.filter(Q(product=product) & Q(feature__feature_id='C'))
        self.assertEqual(len(prod_feature_qs), 0)

    def test_event_handler_price_archived(self):
        """Mock price archived event"""
        self.create_product_price()

        event = self._load_test_data("2020-08-27/webhook_price_updated_archived.json")
        handle_webhook_event(event)
        price = Price.objects.get(price_id='price_1KHkCLL14ex1CGCieIBu8V2e')
        self.assertFalse(price.active)

    def test_event_handler_product_archived(self):
        """Mock product archived event"""
        self.create_product_price()

        event = self._load_test_data("2020-08-27/webhook_product_updated_archived.json")
        handle_webhook_event(event)
        product = Product.objects.get(product_id='prod_KxfXRXOd7dnLbz')
        self.assertFalse(product.active)
