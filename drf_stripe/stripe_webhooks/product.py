from drf_stripe.models import Product
from drf_stripe.stripe_api.products import create_update_product_features
from drf_stripe.stripe_models.product import StripeProductEventData


def _handle_product_event_data(data: StripeProductEventData):
    product_id = data.object.id
    active = data.object.active
    description = data.object.description
    name = data.object.name

    product, created = Product.objects.update_or_create(product_id=product_id, defaults={
        "active": active,
        "description": description,
        "name": name
    })

    create_update_product_features(data.object)
