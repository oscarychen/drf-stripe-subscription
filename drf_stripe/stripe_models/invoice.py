from typing import List, Dict, Optional

from pydantic import BaseModel

from .currency import StripeCurrency
from .price import StripePrice


class StripeInvoiceLineItem(BaseModel):
    """Based on https://stripe.com/docs/api/invoices/line_item"""
    id: str
    amount: int
    currency: StripeCurrency
    description: str = None
    metadata: Dict
    period: Dict
    price: StripePrice
    proration: bool
    quantity: int
    type: str
    discount_amounts: Optional[List[Dict]]
    discountable: Optional[bool]
    discounts: Optional[List[str]]
    invoice_item: Optional[str]
    subscription: str


class StripeInvoiceLines(BaseModel):
    """Based on https://stripe.com/docs/api/invoices/object#invoice_object-lines"""
    data: List[StripeInvoiceLineItem]
    has_more: bool
    url: str


class StripeInvoice(BaseModel):
    """Based on https://stripe.com/docs/api/invoices/object"""
    id: str
    auto_advance: Optional[bool]
    charge: str = None
    collection_method: Optional[str]
    currency: str
    customer: str
    description: str = None
    hosted_invoice_url: Optional[str]
    lines: Optional[List[StripeInvoiceLines]]
