from django.db.models import Q
from django.db.transaction import atomic

from drf_stripe.models import Product, Price, Feature, ProductFeature
from .api import stripe_api as stripe
from ..stripe_models.price import StripePrices
from ..stripe_models.product import StripeProducts


@atomic()
def stripe_api_update_products_prices(**kwargs):
    """
    Fetches list of Products and Price from Stripe, updates database.
    :key dict products:  Optional, list of Stripe Products. Used by test.
        If not provided, will be fetched from Stripe API: stripe.Product.list().
    :key dict prices: Optional, list of Stripe Prices. Used by test.
        If not provided, will be fetched from Stripe API: stripe.Price.list().
    """
    _stripe_api_fetch_update_products(**kwargs)
    _stripe_api_fetch_update_prices(**kwargs)


def _stripe_api_fetch_update_products(products=None, **kwargs):
    """
    Fetch list of Stripe Products and updates database.

    :param dict products_response:  Optional, response from calling Stripe API: stripe.Product.list().
        If not provided the Stripe API will be called to fetch a response.
    """
    if products is None:
        products = stripe.Product.list(limit=100)

    products_response = StripeProducts(**products)

    for product_data in products_response.data:
        product, _ = Product.objects.update_or_create(
            product_id=product_data.id,
            defaults={
                "active": product_data.active,
                "description": product_data.description,
                "name": product_data.name
            }
        )
        create_update_product_features(product_data)


def _stripe_api_fetch_update_prices(prices=None, **kwargs):
    """
    Fetch list of Stripe Prices and updates database.

    :param dict prices_response: Optional, response from calling Stripe API: stripe.Price.list().
        If not provided the Stripe API will be called to fetch a response.
    """
    if prices is None:
        prices = stripe.Price.list(limit=100)
    prices_response = StripePrices(**prices)

    for price_data in prices_response.data:
        Price.objects.update_or_create(
            price_id=price_data.id,
            defaults={
                "product_id": price_data.product,
                "nickname": price_data.nickname,
                "price": price_data.unit_amount,
                "freq": get_freq_from_stripe_price(price_data),
                "active": price_data.active
            }
        )


def get_freq_from_stripe_price(price_data):
    """Get 'freq' string from Stripe price data"""
    if price_data.recurring:
        return f"{price_data.recurring.interval}_{price_data.recurring.interval_count}"


@atomic
def create_update_product_features(product_data):
    """
    Create/update Feature instances associated with a Product given product data.
    The features are specified in Stripe Product object metadata.features as space delimited strings.
    See https://stripe.com/docs/api/products/object#product_object-metadata
    """
    if hasattr(product_data, "metadata") and \
            hasattr(product_data.metadata, "features") and \
            product_data.metadata.features:
        features = product_data.metadata.features.split(" ")

        ProductFeature.objects.filter(Q(product_id=product_data.id) & ~Q(feature_id__in=features)).delete()

        for feature_id in features:
            feature_id = feature_id.strip()
            feature, created_new_feature = Feature.objects.get_or_create(
                feature_id=feature_id,
                defaults={"description": feature_id}
            )
            ProductFeature.objects.get_or_create(product_id=product_data.id, feature=feature)

            if created_new_feature:
                print(
                    f"Created new feature_id {feature_id}, please set feature description manually in database.")
