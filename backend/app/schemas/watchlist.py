from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel, Field


class WatchlistGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistGroupUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WatchlistGroupOut(BaseModel):
    id: UUID
    name: str
    bond_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WatchlistGroupBondOut(BaseModel):
    id: UUID
    group_id: UUID
    bond_id: UUID
    order_index: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WatchlistBondReorder(BaseModel):
    bond_ids: List[UUID]


class WatchlistGroupBondWithData(BaseModel):
    id: UUID
    code: str
    name: str
    bond_type: str
    issuer: Optional[str] = None
    coupon_rate: Optional[float] = None
    remaining_term: Optional[float] = None
    credit_rating: Optional[str] = None
    best_bid_price: Optional[float] = None
    best_ask_price: Optional[float] = None
    best_bid_yield: Optional[float] = None
    best_ask_yield: Optional[float] = None
    latest_trade_price: Optional[float] = None
    latest_trade_yield: Optional[float] = None
    spread: Optional[float] = None
    volume_7d: Optional[float] = None
    order_index: int = 0

    model_config = {"from_attributes": True}


class WatchlistGroupDetailOut(BaseModel):
    id: UUID
    name: str
    bonds: List[WatchlistGroupBondWithData]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
