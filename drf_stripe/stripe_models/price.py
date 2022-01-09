from datetime import datetime
from enum import Enum
from typing import Dict, Union, List

from pydantic import BaseModel

from .currency import StripeCurrency
from .product import StripeProduct


class RecurringInterval(Enum):
    MONTH = 'month'
    YEAR = 'year'
    WEEK = 'week'
    DAY = 'day'


class UsageType(Enum):
    METERED = 'metered'
    LICENSED = 'licensed'


class PriceType(Enum):
    ONE_TIME = 'one_time'
    RECURRING = 'recurring'


class StripePriceRecurring(BaseModel):
    aggregate_usage: str = None
    interval: RecurringInterval
    interval_count: int
    usage_type: UsageType


class StripePrice(BaseModel):
    """A single StripePrice, see https://stripe.com/docs/api/prices/object"""
    id: str
    active: bool
    currency: StripeCurrency
    metadata: Dict
    nickname: str = None
    product: Union[str, StripeProduct]
    recurring: StripePriceRecurring = None
    type: PriceType
    unit_amount: int
    created: datetime


class StripePrices(BaseModel):
    """List of StripePrices"""
    url: str
    has_more: bool
    data: List[StripePrice]
