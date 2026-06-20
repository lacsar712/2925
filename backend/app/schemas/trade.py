from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class TradeOut(BaseModel):
    id: UUID
    bond_id: UUID
    bond_code: Optional[str] = None
    bond_name: Optional[str] = None
    source_id: UUID
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    price: float
    yield_rate: Optional[float] = None
    volume: float
    amount: Optional[float] = None
    direction: str
    counterparty: Optional[str] = None
    trade_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TradeListOut(BaseModel):
    items: list[TradeOut]
    total: int
    page: int
    page_size: int


class TradeStatistics(BaseModel):
    total_volume: float
    total_amount: float
    trade_count: int
    avg_price: Optional[float] = None
    avg_yield: Optional[float] = None
    by_source: list[dict]
    by_bond_type: list[dict]


class FuturesQuoteOut(BaseModel):
    id: UUID
    contract_code: str
    contract_type: str
    latest_price: float
    settlement_price: Optional[float] = None
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    prev_close: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    basis: Optional[float] = None
    quote_time: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SwapQuoteOut(BaseModel):
    id: UUID
    bond_id: UUID
    bond_code: Optional[str] = None
    bond_name: Optional[str] = None
    dealer: str
    swap_rate: float
    tenor: str
    direction: str
    notional_min: Optional[float] = None
    quote_time: Optional[datetime] = None

    model_config = {"from_attributes": True}
