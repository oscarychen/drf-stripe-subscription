from pydantic import ValidationError
from rest_framework.request import Request

from drf_stripe.settings import drf_stripe_settings
from drf_stripe.stripe_api.api import stripe_api as stripe
from drf_stripe.stripe_models.event import EventType
from drf_stripe.stripe_models.event import StripeEvent
from .customer_subscription import _handle_customer_subscription_event_data
from .price import _handle_price_event_data
from .product import _handle_product_event_data


def handle_stripe_webhook_request(request):
    event = _make_webhook_event_from_request(request)
    handle_webhook_event(event)


def _make_webhook_event_from_request(request: Request):
    """
    Given a Rest Framework request, construct a webhook event.

    :param event: event from Stripe Webhook, defaults to None. Used for test.
    """

    return stripe.Webhook.construct_event(
        payload=request.body,
        sig_header=request.META['HTTP_STRIPE_SIGNATURE'],
        secret=drf_stripe_settings.STRIPE_WEBHOOK_SECRET)


def _handle_event_type_validation_error(err: ValidationError):
    """
    Handle Pydantic ValidationError raised when parsing StripeEvent,
    ignores the error if it is caused by unimplemented event.type;
    Otherwise, raise the error.
    """
    event_type_error = False

    for error in err.errors():
        error_loc = error['loc']
        if error_loc[0] == 'event' and error_loc[1] == 'type':
            event_type_error = True
            break

    if event_type_error is False:
        raise err


def handle_webhook_event(event):
    """Perform actions given Stripe Webhook event data."""

    try:
        e = StripeEvent(event=event)
    except ValidationError as err:
        _handle_event_type_validation_error(err)
        return

    event_type = e.event.type

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
   
