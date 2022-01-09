"""
Events that Webhook may receive as part of subscription life cycle

Initial subscription:
- payment_method.attached *
- setup_intent.succeeded
- setup_intent.created
- checkout.session.completed
- invoice.created
- invoice.finalized
- invoice.paid
- invoice.payment_succeeded
- customer.subscription.created

Renewal payment declined:
- charge.failed
- payment_intent.created
- payment_intent.payment_failed
- payment_intent.canceled

Renewal payment successful:
- charge.succeeded
- customer.subscription.trial_will_end *
- invoice.created
- invoice.finalized
- invoice.paid
- invoice.payment_succeeded
- customer.subscription.updated
- payment_intent.succeeded
- payment_intent.created

Subscription cancellation at period end
- customer.subscription.updated

Subscription immediate cancellation
- customer.subscription.deleted


"""

from rest_framework.request import Request

from drf_stripe.settings import drf_stripe_settings
from drf_stripe.stripe_models.event import EventType, StripeSubscriptionEventData
from drf_stripe.stripe_models.event import StripeEvent
from .api import stripe_api as stripe


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
        data = StripeSubscriptionEventData(**e.event.data)
        _webhook_event_customer_subscription_created(data)
    elif event_type is EventType.CUSTOMER_SUBSCRIPTION_UPDATED:
        data = StripeSubscriptionEventData(**e.event.data)
        _webhook_event_customer_subscription_updated(data)
    elif event_type is EventType.CUSTOMER_SUBSCRIPTION_DELETED:
        data = StripeSubscriptionEventData(**e.event.data)
        _webhook_event_customer_subscription_deleted(data)


def _webhook_event_payment_failed(data):
    # print(data)
    pass


def _webhook_event_invoice_paid(data):
    # print(data)
    pass


def _webhook_event_customer_subscription_created(data):
    # print(data)
    pass


def _webhook_event_customer_subscription_updated(data):
    # print(data)
    pass


def _webhook_event_customer_subscription_deleted(data):
    # print(data)
    pass
