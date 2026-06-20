from datetime import date, datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class BondOut(BaseModel):
    id: UUID
    code: str
    name: str
    full_name: Optional[str] = None
    bond_type: str
    issuer: str
    issue_date: Optional[date] = None
    maturity_date: Optional[date] = None
    coupon_rate: Optional[float] = None
    coupon_type: Optional[str] = None
    face_value: Optional[float] = 100.0
    credit_rating: Optional[str] = None
    remaining_term: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BondListOut(BaseModel):
    items: list[BondOut]
    total: int
    page: int
    page_size: int


class BondFilter(BaseModel):
    bond_type: Optional[str] = None
    credit_rating: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20
