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


class BondCalcRequest(BaseModel):
    face_value: float
    coupon_rate: float
    payment_frequency: int
    settlement_date: date
    maturity_date: date
    clean_price: Optional[float] = None
    yield_rate: Optional[float] = None

    model_config = {"from_attributes": True}


class BondCalcResponse(BaseModel):
    face_value: float
    coupon_rate: float
    payment_frequency: int
    settlement_date: date
    maturity_date: date
    clean_price: float
    yield_rate: float
    accrued_interest: float
    dirty_price: float
    macaulay_duration: float
    modified_duration: float
    years_to_maturity: float
    cash_flows: list[dict]

    model_config = {"from_attributes": True}
