from datetime import datetime
from typing import Dict, List, Union, Optional

from pydantic import BaseModel


class PackageDimension(BaseModel):
    height: float = None
    length: float = None
    weight: float = None
    width: float = None


class StripeProductMetadata(BaseModel):
    features: Optional[str] = None


class StripeProduct(BaseModel):
    """A single StripeProduct, see https://stripe.com/docs/api/products/object"""
    id: Optional[str]
    active: Optional[bool]
    description: Optional[str] = None
    metadata: Optional[Union[StripeProductMetadata, Dict]]
    name: Optional[str] = None
    created: Optional[datetime]
    images: Optional[List[str]]
    package_dimensions: Optional[PackageDimension] = None
    shippable: Optional[bool] = None
    statement_descriptor: Optional[str] = None
    tax_code: Optional[Union[str, Dict]] = None
    unit_label: Optional[str] = None
    updated: Optional[datetime] = None
    url: Optional[str] = None


class StripeProducts(BaseModel):
    """List of StripeProducts"""
    url: str
    has_more: bool
    data: List[StripeProduct]


class StripeProductEventData(BaseModel):
    """Based on https://stripe.com/docs/api/products/object"""
    object: StripeProduct
    previous_attributes: Optional[StripeProduct]
