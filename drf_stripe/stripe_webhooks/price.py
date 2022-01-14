from drf_stripe.models import Price
from drf_stripe.stripe_api.products import get_freq_from_stripe_price
from drf_stripe.stripe_models.price import StripePriceEventData


def _handle_price_event_data(data: StripePriceEventData):
    price_id = data.object.id
    product_id = data.object.product
    nickname = data.object.nickname
    price = data.object.unit_amount
    active = data.object.active
    freq = get_freq_from_stripe_price(data.object)

    price_obj, created = Price.objects.update_or_create(
        price_id=price_id,
        defaults={
            "product_id": product_id,
            "nickname": nickname,
            "price": price,
            "active": active,
            "freq": freq
        }
    )
