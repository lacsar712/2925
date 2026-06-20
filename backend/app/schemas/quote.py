from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class QuoteOut(BaseModel):
    id: UUID
    bond_id: UUID
    source_id: UUID
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    bid_price: Optional[float] = None
    ask_price: Optional[float] = None
    bid_yield: Optional[float] = None
    ask_yield: Optional[float] = None
    bid_volume: Optional[float] = None
    ask_volume: Optional[float] = None
    counterparty: Optional[str] = None
    quote_time: Optional[datetime] = None
    is_best: bool = False

    model_config = {"from_attributes": True}


class SourceQuoteSummary(BaseModel):
    source_name: str
    source_type: str
    best_bid_price: Optional[float] = None
    best_ask_price: Optional[float] = None
    best_bid_yield: Optional[float] = None
    best_ask_yield: Optional[float] = None
    quote_count: int = 0
    latest_quote_time: Optional[datetime] = None


class AggregatedQuoteOut(BaseModel):
    bond: "BondBasic"
    sources: list[SourceQuoteSummary]
    best_bid_price: Optional[float] = None
    best_ask_price: Optional[float] = None
    best_bid_yield: Optional[float] = None
    best_ask_yield: Optional[float] = None
    spread: Optional[float] = None
    total_quotes: int = 0


class BondBasic(BaseModel):
    id: UUID
    code: str
    name: str
    bond_type: str
    coupon_rate: Optional[float] = None
    remaining_term: Optional[float] = None

    model_config = {"from_attributes": True}


AggregatedQuoteOut.model_rebuild()
