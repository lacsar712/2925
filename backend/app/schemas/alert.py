from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.bond import BondOut


class AlertRuleBase(BaseModel):
    bond_id: UUID
    alert_type: str = Field(..., pattern="^(yield|net_price)$")
    condition: str = Field(..., pattern="^(above|below)$")
    threshold: float = Field(..., gt=0)
    is_enabled: Optional[bool] = True
    trigger_cooldown_minutes: Optional[int] = Field(5, ge=1, le=1440)
    description: Optional[str] = Field(None, max_length=500)


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    alert_type: Optional[str] = Field(None, pattern="^(yield|net_price)$")
    condition: Optional[str] = Field(None, pattern="^(above|below)$")
    threshold: Optional[float] = Field(None, gt=0)
    is_enabled: Optional[bool] = None
    trigger_cooldown_minutes: Optional[int] = Field(None, ge=1, le=1440)
    description: Optional[str] = Field(None, max_length=500)


class AlertRuleOut(AlertRuleBase):
    id: UUID
    user_id: UUID
    bond: Optional[BondOut] = None
    last_triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertRuleListOut(BaseModel):
    items: list[AlertRuleOut]
    total: int
    page: int
    page_size: int


class AlertTriggerOut(BaseModel):
    id: UUID
    rule_id: UUID
    user_id: UUID
    bond_id: UUID
    bond: Optional[BondOut] = None
    alert_type: str
    condition: str
    threshold: float
    actual_value: float
    is_read: bool
    message: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertTriggerListOut(BaseModel):
    items: list[AlertTriggerOut]
    total: int
    page: int
    page_size: int


class UnreadCountOut(BaseModel):
    count: int


class MarkReadRequest(BaseModel):
    trigger_ids: Optional[list[UUID]] = Field(None, description="要标记已读的触发记录ID列表，为空则标记全部")


class AlertRuleToggleOut(BaseModel):
    id: UUID
    is_enabled: bool
    message: str
