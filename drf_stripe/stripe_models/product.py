from datetime import datetime
from enum import Enum
from typing import Dict, List, Union, Optional

from pydantic import BaseModel


class PackageDimension(Enum):
    height: float
    length: float
    weight: float
    width: float


class StripeProductMetadata(BaseModel):
    features: Optional[str] = None


class StripeProduct(BaseModel):
    """A single StripeProduct, see https://stripe.com/docs/api/products/object"""
    id: str
    active: bool
    description: str = None
    metadata: Union[StripeProductMetadata, Dict]
    name: str = None
    created: datetime
    images: List[str]
    package_dimensions: PackageDimension = None
    shippable: bool = None
    statement_descriptor: str = None
    tax_code: Union[str, Dict] = None
    unit_label: str = None
    updated: datetime = None
    url: str = None


class StripeProducts(BaseModel):
    """List of StripeProducts"""
    url: str
    has_more: bool
    data: List[StripeProduct]
