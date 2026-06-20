from datetime import datetime
from uuid import UUID
from typing import Optional, Any

from pydantic import BaseModel, Field


class AuditLogOut(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    username: str
    action_type: str
    action_target: Optional[str] = None
    action_summary: str
    detail: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


class AuditActionType(BaseModel):
    key: str
    label: str


AUDIT_ACTION_TYPES: list[AuditActionType] = [
    AuditActionType(key="user_login", label="用户登录"),
    AuditActionType(key="user_logout", label="用户登出"),
    AuditActionType(key="user_login_failed", label="登录失败"),
    AuditActionType(key="favorite_add", label="添加收藏"),
    AuditActionType(key="favorite_remove", label="取消收藏"),
    AuditActionType(key="source_enable", label="启用行情源"),
    AuditActionType(key="source_disable", label="禁用行情源"),
    AuditActionType(key="source_update", label="更新行情源"),
    AuditActionType(key="user_create", label="创建用户"),
    AuditActionType(key="user_update", label="更新用户"),
    AuditActionType(key="user_delete", label="删除用户"),
    AuditActionType(key="cache_refresh", label="刷新缓存"),
    AuditActionType(key="watchlist_group_create", label="创建分组"),
    AuditActionType(key="watchlist_group_update", label="更新分组"),
    AuditActionType(key="watchlist_group_delete", label="删除分组"),
    AuditActionType(key="alert_rule_create", label="创建预警规则"),
    AuditActionType(key="alert_rule_update", label="更新预警规则"),
    AuditActionType(key="alert_rule_delete", label="删除预警规则"),
]
