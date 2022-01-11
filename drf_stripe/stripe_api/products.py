from django.db.models import Q
from django.db.transaction import atomic

from drf_stripe.models import Product, Price, Feature, ProductFeature
from .api import stripe_api as stripe
from ..stripe_models.price import StripePrices
from ..stripe_models.product import StripeProducts


@atomic()
def stripe_api_update_products_prices():
    """
    Fetches list of Products and Price from Stripe, updates database.
    """
    _stripe_api_fetch_update_products()
    _stripe_api_fetch_update_prices()


def _stripe_api_fetch_update_products():
    """
    Fetch list of Stripe Products and updates database.
    """
    products_response = StripeProducts(**stripe.Product.list(limit=100))

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


def _stripe_api_fetch_update_prices():
    """
    Fetch list of Stripe Prices and updates database.
    """
    prices_response = StripePrices(**stripe.Price.list(limit=100))

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
        return f"{price_data.recurring.interval.value}_{price_data.recurring.interval_count}"


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
