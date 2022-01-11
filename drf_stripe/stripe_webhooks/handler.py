from rest_framework.request import Request

from drf_stripe.settings import drf_stripe_settings
from drf_stripe.stripe_api.api import stripe_api as stripe
from drf_stripe.stripe_models.event import EventType
from drf_stripe.stripe_models.event import StripeEvent
from .customer_subscription import _handle_customer_subscription_event_data
from .price import _handle_price_event_data
from .product import _handle_product_event_data


def handle_stripe_webhook_request(request):
    event = _make_webhook_event(request)
    _handle_webhook_event(event)


def _make_webhook_event(request: Request):
    event = stripe.Webhook.construct_event(
        payload=request.body,
        sig_header=request.META['HTTP_STRIPE_SIGNATURE'],
        secret=drf_stripe_settings.STRIPE_WEBHOOK_SECRET)

    return StripeEvent(event=event)


def _handle_webhook_event(e: StripeEvent):
    print(e.event.type)
    try:
        event_type = EventType(e.event.type)
    except ValueError:
        return

    if event_type is EventType.CUSTOMER_SUBSCRIPTION_CREATED:
        _handle_customer_subscription_event_data(e.event.data)
    elif event_type is EventType.CUSTOMER_SUBSCRIPTION_UPDATED:
        _handle_customer_subscription_event_data(e.event.data)
    elif event_type is EventType.CUSTOMER_SUBSCRIPTION_DELETED:
        _handle_customer_subscription_event_data(e.event.data)

    elif event_type is EventType.PRODUCT_CREATED:
        _handle_product_event_data(e.event.data)
    elif event_type is EventType.PRODUCT_UPDATED:
        _handle_product_event_data(e.event.data)
    elif event_type is EventType.PRODUCT_DELETED:
        _handle_product_event_data(e.event.data)

    elif event_type is EventType.PRICE_CREATED:
        _handle_price_event_data(e.event.data)
    elif event_type is EventType.PRICE_UPDATED:
        _handle_price_event_data(e.event.data)
    elif event_type is EventType.PRICE_DELETED:
        _handle_price_event_data(e.event.data)
