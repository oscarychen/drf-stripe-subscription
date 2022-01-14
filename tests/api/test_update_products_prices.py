from drf_stripe.models import Product, Price, Feature, ProductFeature
from tests.base import BaseTest


class TestProductInitialization(BaseTest):
    def setUp(self) -> None:
        self.setup_product_prices()

    def test_products_prices_initialization(self):
        """
        Check products and prices have been set up properly in database.
        This tests drf_stripe.stripe_api.products.stripe_api_update_products_prices()
        which is the core of the 'update_stripe_products' management command.
        """

        prod_abc = Product.objects.get(product_id='prod_KxgA5goLUMwnoN')
        prod_abd = Product.objects.get(product_id='prod_KxfXRXOd7dnLbz')

        price_abc1 = Price.objects.get(price_id='price_1KHkoTL14ex1CGCiV8X4cJs5')

        price_abd1 = Price.objects.get(price_id='price_1KHkCLL14ex1CGCipzcBdnOp')
        price_abd2 = Price.objects.get(price_id='price_1KHkCLL14ex1CGCieIBu8V2e')

        feature_a = Feature.objects.get(feature_id='A')
        feature_b = Feature.objects.get(feature_id='B')
        feature_c = Feature.objects.get(feature_id='C')
        feature_d = Feature.objects.get(feature_id='D')

        # Check product-to-feature relations
        ProductFeature.objects.get(product=prod_abc, feature=feature_a)
        ProductFeature.objects.get(product=prod_abc, feature=feature_b)
        ProductFeature.objects.get(product=prod_abc, feature=feature_c)
        ProductFeature.objects.get(product=prod_abd, feature=feature_a)
        ProductFeature.objects.get(product=prod_abd, feature=feature_b)
        ProductFeature.objects.get(product=prod_abd, feature=feature_d)
        self.assertEqual(len(ProductFeature.objects.filter(product=prod_abc, feature=feature_d)), 0)
        self.assertEqual(len(ProductFeature.objects.filter(product=prod_abd, feature=feature_c)), 0)

        # Check price-to-product relations
        self.assertEqual(price_abc1.product.product_id, prod_abc.product_id)
        self.assertEqual(price_abd1.product.product_id, prod_abd.product_id)
        self.assertEqual(price_abd2.product.product_id, prod_abd.product_id)
