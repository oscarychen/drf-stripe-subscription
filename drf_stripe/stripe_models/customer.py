from datetime import datetime
from typing import Optional, Dict, Union, List

from pydantic import BaseModel

from .currency import StripeCurrency
from .subscription import StripeSubscriptionItems


class StripeCustomer(BaseModel):
    """Based on https://stripe.com/docs/api/customers/object"""
    id: str
    address: Optional[Dict] = None
    description: Optional[str] = None
    email: Optional[str]
    metadata: Optional[Dict]
    name: Optional[str] = None
    phone: Optional[str] = None
    shipping: Optional[Dict] = None
    balance: Optional[int] = None
    created: Optional[datetime]
    currency: Optional[StripeCurrency] = None
    default_source: Optional[Union[str, Dict]] = None
    delinquent: Optional[bool]
    discount: Optional[Dict] = None
    invoice_prefix: Optional[str]
    invoice_settings: Optional[Dict]
    livemode: Optional[bool]
    next_invoice_sequence: Optional[int]
    preferred_locales: Optional[List[str]]
    sources: Optional[List[Dict]]
    subscriptions: Optional[List[StripeSubscriptionItems]]
    tax: Optional[Dict]
    tax_exempt: Optional[str]
    tax_ids: Optional[List[Dict]]


class StripeCustomers(BaseModel):
    """Based on https://stripe.com/docs/api/customers/list"""
    data: List[StripeCustomer]
    has_more: bool = None
    url: str = None
