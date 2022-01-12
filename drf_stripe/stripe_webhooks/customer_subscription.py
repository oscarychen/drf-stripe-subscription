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
- invoice.payment_failed
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

from django.contrib.auth import get_user_model

from drf_stripe.models import Subscription, SubscriptionItem
from drf_stripe.stripe_models.event import StripeSubscriptionEventData


def _handle_customer_subscription_event_data(data: StripeSubscriptionEventData):
    subscription_id = data.object.id
    customer = data.object.customer
    period_start = data.object.current_period_start
    period_end = data.object.current_period_end
    cancel_at_period_end = data.object.cancel_at_period_end
    cancel_at = data.object.cancel_at
    ended_at = data.object.ended_at
    status = data.object.status
    trial_end = data.object.trial_end
    trial_start = data.object.trial_start
    items = data.object.items

    user = get_user_model().objects.get(stripe_user__customer_id=customer)

    subscription, created = Subscription.objects.update_or_create(
        subscription_id=subscription_id,
        defaults={
            "user": user,
            "period_start": period_start,
            "period_end": period_end,
            "cancel_at": cancel_at,
            "cancel_at_period_end": cancel_at_period_end,
            "ended_at": ended_at,
            "status": status,
            "trial_end": trial_end,
            "trial_start": trial_start
        })

    print(
        f"{subscription} created={created} status={status}, cancel_at={cancel_at}, cancel_at_period_end={cancel_at_period_end}, trial_end={trial_end}, period_start={period_start}, period_end={period_end}")

    for item in items.data:
        item_id = item.id
        price = item.price.id
        quantity = item.quantity
        SubscriptionItem.objects.update_or_create(
            sub_item_id=item_id,
            defaults={
                "subscription": subscription,
                "price_id": price,
                "quantity": quantity
            }
        )
