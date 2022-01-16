from drf_stripe.models import Subscription, SubscriptionItem, StripeUser
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

    stripe_user = StripeUser.objects.get(customer_id=customer)

    subscription, created = Subscription.objects.update_or_create(
        subscription_id=subscription_id,
        defaults={
            "stripe_user": stripe_user,
            "period_start": period_start,
            "period_end": period_end,
            "cancel_at": cancel_at,
            "cancel_at_period_end": cancel_at_period_end,
            "ended_at": ended_at,
            "status": status,
            "trial_end": trial_end,
            "trial_start": trial_start
        })

    subscription.items.all().delete()
    _create_subscription_items(data)


def _create_subscription_items(data: StripeSubscriptionEventData):
    for item in data.object.items.data:
        SubscriptionItem.objects.update_or_create(
            sub_item_id=item.id,
            defaults={
                "subscription_id": data.object.id,
                "price_id": item.price.id,
                "quantity": item.quantity
            }
        )
