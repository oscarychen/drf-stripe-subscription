from typing import List, Dict

from pydantic import BaseModel


class StripeSubscriptionItemsDataItem(BaseModel):
    """Based on https://stripe.com/docs/api/subscriptions/object#subscription_object-items-data"""
    id: str
    billing_thresholds: Dict = None
    created: int
    metadata: Dict
    price: Dict
    quantity: int
    subscription: str
    tax_rates: List


class StripeSubscriptionItems(BaseModel):
    """Based on https://stripe.com/docs/api/subscriptions/object#subscription_object-items"""
    data: List[StripeSubscriptionItemsDataItem]
    has_more: bool
    url: str


class StripeSubscription(BaseModel):
    """Based on https://stripe.com/docs/api/subscriptions/object"""
    id: str
    cancel_at_period_end: bool
    current_period_end: int
    current_period_start: int
    customer: str
    default_payment_method: str
    items: StripeSubscriptionItems
    latest_invoice: str
    metadata: Dict
    pending_setup_intent: str = None
    pending_update: str = None
    status: str
