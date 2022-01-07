from enum import Enum
from typing import Optional, Union, Literal, Any

from pydantic import BaseModel, Field

from .invoice import StripeInvoice
from .subscription import StripeSubscription


class EventType(Enum):
    """See: https://stripe.com/docs/api/events/types"""

    CUSTOMER_UPDATED = 'customer.updated'
    INVOICE_CREATED = 'invoice.created'
    INVOICE_FINALIZED = 'invoice.finalized'
    INVOICE_PAYMENT_SUCCEEDED = 'invoice.payment_succeeded'
    INVOICE_PAYMENT_FAILED = 'invoice.payment_failed'
    INVOICE_PAID = 'invoice.paid'
    CUSTOMER_SUBSCRIPTION_UPDATED = 'customer.subscription.updated'
    CUSTOMER_SUBSCRIPTION_DELETED = 'customer.subscription.deleted'
    INVOICEITEM_CREATED = 'invoiceitem.created'


class StripeEventRequest(BaseModel):
    """Based on: https://stripe.com/docs/api/events/object#event_object-request"""
    id: str = None
    idempotency_key: str = None


class StripeBaseEvent(BaseModel):
    """Based on https://stripe.com/docs/api/events/object"""
    id: str
    api_version: str
    request: StripeEventRequest
    data: Any  # overwrite this attribute when inheriting
    type: str  # overwrite this attribute when inheriting


"""
Invoice event classes
"""


class StripeInvoiceEventData(BaseModel):
    """Based on https://stripe.com/docs/api/events/object#event_object-data"""
    object: StripeInvoice
    previous_attributes: Optional[StripeInvoice]


class StripeInvoiceEvent(StripeBaseEvent):
    data: StripeInvoiceEventData
    type: Literal[
        EventType.INVOICE_PAID,
        EventType.INVOICE_CREATED,
        EventType.INVOICE_PAID,
        EventType.INVOICE_PAYMENT_FAILED
    ]


"""
Subscription event classes
"""


class StripeSubscriptionEventData(BaseModel):
    """Based on https://stripe.com/docs/api/events/object#event_object-data"""
    object: StripeSubscription
    previous_attributes: Optional[StripeSubscription]


class StripeSubscriptionEvent(StripeBaseEvent):
    data: StripeSubscriptionEventData
    type: Literal[
        EventType.CUSTOMER_SUBSCRIPTION_DELETED,
        EventType.CUSTOMER_SUBSCRIPTION_UPDATED
    ]


class StripeEvent(BaseModel):
    # Add event classes to this attribute as they are implemented, more specific types first.
    # see https://pydantic-docs.helpmanual.io/usage/types/#discriminated-unions-aka-tagged-unions
    event: Union[StripeSubscriptionEvent, StripeInvoiceEvent, StripeBaseEvent] = Field(...,
                                                                                       discriminator='type')
