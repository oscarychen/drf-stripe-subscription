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
    :key dict test_products: mock event data for testing
    :key dict test_prices: mock event data for testing
    """
    _stripe_api_fetch_update_products(**kwargs)
    _stripe_api_fetch_update_prices(**kwargs)


def _stripe_api_fetch_update_products(test_products=None, **kwargs):
    """
    Fetch list of Stripe Products and updates database.

    :param dict test_products:  Response from calling Stripe API: stripe.Product.list(). Used for testing.
    """
    if test_products is None:
        products_data = stripe.Product.list(limit=100)
    else:
        products_data = test_products

    products = StripeProducts(**products_data).data

    creation_count = 0
    for product in products:
        product_obj, created = Product.objects.update_or_create(
            product_id=product.id,
            defaults={
                "active": product.active,
                "description": product.description,
                "name": product.name
            }
        )
        create_update_product_features(product)
        if created is True:
            creation_count += 1

    print(f"Created {creation_count} new Products")


def _stripe_api_fetch_update_prices(test_prices=None, **kwargs):
    """
    Fetch list of Stripe Prices and updates database.

    :param dict test_prices: Optional, response from calling Stripe API: stripe.Price.list(). Used for testing.
    """
    if test_prices is None:
        prices_data = stripe.Price.list(limit=100)
    else:
        prices_data = test_prices

    prices = StripePrices(**prices_data).data

    creation_count = 0
    for price in prices:
        price_obj, created = Price.objects.update_or_create(
            price_id=price.id,
            defaults={
                "product_id": price.product,
                "nickname": price.nickname,
                "price": price.unit_amount,
                "freq": get_freq_from_stripe_price(price),
                "active": price.active
            }
        )
        if created is True:
            creation_count += 1

    print(f"Created {creation_count} new Prices")


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
