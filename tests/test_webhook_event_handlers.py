import json
from pathlib import Path

from django.db.models import Q
from django.test import TestCase

from drf_stripe.models import Product, Price, Feature, ProductFeature
from drf_stripe.stripe_api.products import stripe_api_update_products_prices
from drf_stripe.stripe_webhooks.handler import handle_webhook_event


class BaseTest(TestCase):
    def setUp(self) -> None:
        products = self._load_test_data("v1/stripe_product_list.json")
        prices = self._load_test_data("v1/stripe_price_list.json")
        stripe_api_update_products_prices(products=products, prices=prices)

    def tearDown(self) -> None:
        pass

    @staticmethod
    def _load_test_data(file_name):
        p = Path("tests/mock_responses") / file_name
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return data

    @staticmethod
    def _print(v):
        print("$$$$$$$ DEBUG $$$$$")
        print(v)
        assert False


class TestProductInitialization(BaseTest):

    def test_products_prices_initialization(self):
        """
        Check products and prices have been set up properly in database.
        This tests drf_stripe.stripe_api.products.stripe_api_update_products_prices()
        which is the core of the 'update_stripe_products' management command.
        """

        prod_abc = Product.objects.get(product_id='prod_abc')
        prod_bcd = Product.objects.get(product_id='prod_bcd')

        price_abc1 = Price.objects.get(price_id='price_abc1')
        price_abc2 = Price.objects.get(price_id='price_abc2')
        price_bcd1 = Price.objects.get(price_id='price_bcd1')
        price_bcd2 = Price.objects.get(price_id='price_bcd2')

        feature_a = Feature.objects.get(feature_id='A')
        feature_b = Feature.objects.get(feature_id='B')
        feature_c = Feature.objects.get(feature_id='C')
        feature_d = Feature.objects.get(feature_id='D')

        # Check product-to-feature relations
        ProductFeature.objects.get(product=prod_abc, feature=feature_a)
        ProductFeature.objects.get(product=prod_abc, feature=feature_b)
        ProductFeature.objects.get(product=prod_abc, feature=feature_c)
        ProductFeature.objects.get(product=prod_bcd, feature=feature_b)
        ProductFeature.objects.get(product=prod_bcd, feature=feature_c)
        ProductFeature.objects.get(product=prod_bcd, feature=feature_d)

        # Check price-to-product relations
        self.assertEqual(price_abc1.product, prod_abc)
        self.assertEqual(price_abc2.product, prod_abc)
        self.assertEqual(price_bcd1.product, prod_bcd)
        self.assertEqual(price_bcd2.product, prod_bcd)


class TestWebhookProductPriceUpdates(BaseTest):

    def test_event_handler_product_created(self):
        """
        Mock production and price creation events
        """
        product_created = self._load_test_data("v1/webhook_product_created.json")
        price_created = self._load_test_data("v1/webhook_price_created.json")

        # send mock webhook events
        handle_webhook_event(product_created)
        handle_webhook_event(price_created)

        # check product and price created
        product_ac = Product.objects.get(product_id='prod_ac')
        price_ac1 = Price.objects.get(price_id='price_ac1')

        # check Product-to-Price relation created
        self.assertEqual(price_ac1.product, product_ac)

        # check Product-to-Feature relations created
        ProductFeature.objects.get(product=product_ac, feature__feature_id='A')
        ProductFeature.objects.get(product=product_ac, feature__feature_id='C')

    def test_event_handler_product_update(self):
        """
        Mock product and price update events
        """

        # create a product and price
        product_created = self._load_test_data("v1/webhook_product_created.json")
        price_created = self._load_test_data("v1/webhook_price_created.json")
        handle_webhook_event(product_created)
        handle_webhook_event(price_created)

        # modify price
        price_mod = self._load_test_data("v1/webhook_price_updated.json")
        handle_webhook_event(price_mod)

        # check price modifications
        price_ac1 = Price.objects.get(price_id='price_ac1')
        self.assertEqual(price_ac1.price, 127)
        self.assertEqual(price_ac1.freq, "year_1")
        self.assertEqual(price_ac1.nickname, "Test pricing yearly")
        self.assertEqual(price_ac1.product.product_id, "prod_ac")

        # modify product
        product_mod = self._load_test_data("v1/webhook_product_updated.json")
        handle_webhook_event(product_mod)

        # check product modifications
        product_ac = Product.objects.get(product_id='prod_ac')
        self.assertEqual(product_ac.name, "Test Product Modified")
        self.assertEqual(product_ac.description, "Modified product")

        # check product is now associated with feature D
        ProductFeature.objects.get(product=product_ac, feature__feature_id='D')

        # check product no longer associated with feature C
        prod_feature_qs = ProductFeature.objects.filter(Q(product=product_ac) & Q(feature__feature_id='C'))
        self.assertEqual(len(prod_feature_qs), 0)

        # delete price
        price_del = self._load_test_data("v1/webhook_price_deleted.json")
        handle_webhook_event(price_del)
        price_ac1 = Price.objects.get(price_id='price_ac1')
        self.assertEqual(price_ac1.active, False)

        # delete product
        prod_del = self._load_test_data("v1/webhook_product_deleted.json")
        handle_webhook_event(prod_del)
        product_ac = Product.objects.get(product_id='prod_ac')
        self.assertEqual(product_ac.active, False)
