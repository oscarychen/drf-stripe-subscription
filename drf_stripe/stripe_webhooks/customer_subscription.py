from drf_stripe.models import Subscription, SubscriptionItem, StripeUser
from drf_stripe.stripe_api.customers import get_billing_model, find_billing_account, update_billing_account_subscription
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

    subscription_defaults = {
        "stripe_user": stripe_user,
        "period_start": period_start,
        "period_end": period_end,
        "cancel_at": cancel_at,
        "cancel_at_period_end": cancel_at_period_end,
        "ended_at": ended_at,
        "status": status,
        "trial_end": trial_end,
        "trial_start": trial_start
    }

    # Link to billing account if configured
    billing_model = get_billing_model()
    if billing_model:
        user = stripe_user.user if stripe_user else None
        billing_account = find_billing_account(billing_model, customer_id=customer, user=user)
        subscription_defaults = update_billing_account_subscription(
            billing_model, billing_account, customer, subscription_id, subscription_defaults
        )

    subscription, created = Subscription.objects.update_or_create(
        subscription_id=subscription_id,
        defaults=subscription_defaults
    )

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
