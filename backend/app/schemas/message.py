from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel, Field


class MessageLink(BaseModel):
    type: str
    params: dict[str, str] = Field(default_factory=dict)


class MessageOut(BaseModel):
    id: UUID
    type: str
    title: str
    content: str
    is_read: bool
    link: Optional[MessageLink] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MessageListOut(BaseModel):
    items: list[MessageOut]
    total: int
    page: int
    page_size: int


class UnreadCountByTypeOut(BaseModel):
    announcement: int = 0
    market_movement: int = 0
    price_alert: int = 0
    admin_broadcast: int = 0
    total: int = 0


class MessageCreate(BaseModel):
    type: str = Field(..., pattern="^(announcement|market_movement|price_alert|admin_broadcast)$")
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    link: Optional[MessageLink] = None
    metadata: Optional[dict[str, Any]] = None
    user_id: Optional[UUID] = Field(None, description="指定接收用户，管理员广播时可省略")


class MarkAllReadRequest(BaseModel):
    type: Optional[str] = Field(None, pattern="^(announcement|market_movement|price_alert|admin_broadcast)$")
