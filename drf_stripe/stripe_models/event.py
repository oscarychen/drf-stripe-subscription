from enum import Enum
from typing import Union, Literal, Any

from pydantic import BaseModel, Field

from .invoice import StripeInvoiceEventData
from .price import StripePriceEventData
from .product import StripeProductEventData
from .subscription import StripeSubscriptionEventData


class EventType(str, Enum):
    """See: https://stripe.com/docs/api/events/types"""

    CUSTOMER_UPDATED = 'customer.updated'

    CUSTOMER_SUBSCRIPTION_CREATED = 'customer.subscription.created'
    CUSTOMER_SUBSCRIPTION_UPDATED = 'customer.subscription.updated'
    CUSTOMER_SUBSCRIPTION_DELETED = 'customer.subscription.deleted'

    INVOICE_CREATED = 'invoice.created'
    INVOICE_FINALIZED = 'invoice.finalized'
    INVOICE_PAYMENT_SUCCEEDED = 'invoice.payment_succeeded'
    INVOICE_PAYMENT_FAILED = 'invoice.payment_failed'
    INVOICE_PAID = 'invoice.paid'

    INVOICEITEM_CREATED = 'invoiceitem.created'

    PRODUCT_CREATED = 'product.created'
    PRODUCT_UPDATED = 'product.updated'
    PRODUCT_DELETED = 'product.deleted'

    PRICE_DELETED = 'price.deleted'
    PRICE_UPDATED = 'price.updated'
    PRICE_CREATED = 'price.created'


class StripeEventRequest(BaseModel):
    """Based on: https://stripe.com/docs/api/events/object#event_object-request"""
    id: str = None
    idempotency_key: str = None


class StripeBaseEvent(BaseModel):
    """
    Based on https://stripe.com/docs/api/events/object
    This is the base event template for more specific Stripe event classes
    """
    id: str
    api_version: str
    request: StripeEventRequest
    data: Any  # overwrite this attribute when inheriting
    type: Literal[str]  # overwrite this attribute when inheriting


class StripeInvoiceEvent(StripeBaseEvent):
    data: StripeInvoiceEventData
    type: Literal[
        EventType.INVOICE_PAID,
        EventType.INVOICE_CREATED,
        EventType.INVOICE_PAID,
        EventType.INVOICE_PAYMENT_FAILED
    ]


class StripeSubscriptionEvent(StripeBaseEvent):
    data: StripeSubscriptionEventData
    type: Literal[
        EventType.CUSTOMER_SUBSCRIPTION_DELETED,
        EventType.CUSTOMER_SUBSCRIPTION_UPDATED,
        EventType.CUSTOMER_SUBSCRIPTION_CREATED
    ]


class StripeProductEvent(StripeBaseEvent):
    data: StripeProductEventData
    type: Literal[
        EventType.PRODUCT_UPDATED,
        EventType.PRODUCT_CREATED,
        EventType.PRODUCT_DELETED
    ]


class StripePriceEvent(StripeBaseEvent):
    data: StripePriceEventData
    type: Literal[
        EventType.PRICE_CREATED,
        EventType.PRICE_UPDATED,
        EventType.PRICE_DELETED
    ]


class StripeEvent(BaseModel):
    # Add event classes to this attribute as they are implemented, more specific types first.
    # see https://pydantic-docs.helpmanual.io/usage/types/#discriminated-unions-aka-tagged-unions
    event: Union[
        StripeSubscriptionEvent,
        StripeInvoiceEvent,
        StripeProductEvent,
        StripePriceEvent,
        StripeBaseEvent,  # needed here so unimplemented event types can pass through validation
    ] = Field(discriminator='type')
