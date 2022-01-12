from datetime import datetime
from enum import Enum
from typing import Dict, Union, List, Optional

from pydantic import BaseModel

from .currency import StripeCurrency
from .product import StripeProduct


class RecurringInterval(str, Enum):
    MONTH = 'month'
    YEAR = 'year'
    WEEK = 'week'
    DAY = 'day'


class UsageType(str, Enum):
    METERED = 'metered'
    LICENSED = 'licensed'


class PriceType(str, Enum):
    ONE_TIME = 'one_time'
    RECURRING = 'recurring'


class StripePriceRecurring(BaseModel):
    aggregate_usage: str = None
    interval: RecurringInterval
    interval_count: Optional[int]
    usage_type: Optional[UsageType]


class StripePrice(BaseModel):
    """A single StripePrice, see https://stripe.com/docs/api/prices/object"""
    id: Optional[str]
    active: Optional[bool]
    currency: Optional[StripeCurrency]
    metadata: Optional[Dict]
    nickname: Optional[str] = None
    product: Optional[Union[str, StripeProduct]]
    recurring: Optional[StripePriceRecurring] = None
    type: Optional[PriceType]
    unit_amount: Optional[int]
    created: Optional[datetime]


class StripePrices(BaseModel):
    """List of StripePrices"""
    url: str
    has_more: bool
    data: List[StripePrice]


class StripePriceEventData(BaseModel):
    """Based on https://stripe.com/docs/api/prices/object"""
    object: StripePrice
    previous_attributes: Optional[StripePrice]
