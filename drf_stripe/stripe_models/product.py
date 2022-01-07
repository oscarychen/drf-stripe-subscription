from datetime import datetime
from enum import Enum
from typing import Dict, List, Union

from pydantic import BaseModel


class PackageDimension(Enum):
    height: float
    length: float
    weight: float
    width: float


class StripeProduct(BaseModel):
    """See: https://stripe.com/docs/api/products/object"""
    id: str
    active: bool
    description: str
    metadata: Dict
    name: str
    created: datetime
    images: List[str]
    package_dimensions: PackageDimension = None
    shippable: bool = None
    statement_descriptor: str = None
    tax_code: Union[str, Dict] = None
    unit_label: str
    updated: datetime
    url: str
