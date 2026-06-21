from uuid import UUID
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import MarketSource
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.schemas.audit import AuditLogOut, AuditLogListResponse, AUDIT_ACTION_TYPES
from app.api.deps import require_admin
from app.services.cache_service import CacheService
from app.services.audit_service import log_audit, get_client_ip, get_user_agent
from passlib.context import CryptContext

router = APIRouter(prefix="/api/admin", tags=["系统管理"])


@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    result = await db.execute(select(MarketSource).order_by(MarketSource.name))
    sources = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "source_type": s.source_type,
            "status": s.status,
            "description": s.description,
            "is_enabled": s.is_enabled,
        }
        for s in sources
    ]


@router.put("/sources/{source_id}")
async def update_source(
    source_id: UUID,
    body: dict,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(MarketSource).where(MarketSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="行情源不存在")

    old_enabled = source.is_enabled
    old_status = source.status
    changes = {}

    if "status" in body:
        changes["status"] = {"old": old_status, "new": body["status"]}
        source.status = body["status"]
    if "is_enabled" in body:
        changes["is_enabled"] = {"old": old_enabled, "new": body["is_enabled"]}
        source.is_enabled = body["is_enabled"]
    if "description" in body:
        changes["description"] = {"old": source.description, "new": body["description"]}
        source.description = body["description"]

    await db.flush()

    ip = get_client_ip(request)
    action_type = "source_update"
    summary = f"更新行情源：{source.name}"

    if "is_enabled" in changes:
        changes_enabled = changes["is_enabled"]
        if changes_enabled["new"] and not changes_enabled["old"]:
            action_type = "source_enable"
            summary = f"启用行情源：{source.name}"
        elif not changes_enabled["new"] and changes_enabled["old"]:
            action_type = "source_disable"
            summary = f"禁用行情源：{source.name}"

    await log_audit(
        user=admin,
        action_type=action_type,
        action_target=source.name,
        action_summary=summary,
        detail={
            "source_id": str(source_id),
            "source_name": source.name,
            "changes": changes,
        },
        ip_address=ip,
        db=db,
    )

    return {"message": "更新成功"}


@router.get("/users", response_model=list[UserOut])
async def get_users(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    result = await db.execute(select(User).order_by(User.created_at))
    return [UserOut.model_validate(u) for u in result.scalars().all()]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    user = User(
        username=body.username,
        password_hash=pwd_context.hash(body.password),
        display_name=body.display_name,
        role=body.role,
        department=body.department,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    ip = get_client_ip(request)
    await log_audit(
        user=admin,
        action_type="user_create",
        action_target=body.username,
        action_summary=f"创建用户：{body.username} ({body.display_name})",
        detail={
            "target_user_id": str(user.id),
            "target_username": body.username,
            "target_display_name": body.display_name,
            "target_role": body.role,
            "target_department": body.department,
        },
        ip_address=ip,
        db=db,
    )

    return UserOut.model_validate(user)


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_values = {
        "display_name": user.display_name,
        "role": user.role,
        "department": user.department,
        "is_active": user.is_active,
    }

    update_data = body.model_dump(exclude_unset=True)
    changes = {}

    if "password" in update_data:
        user.password_hash = pwd_context.hash(update_data["password"])
        changes["password"] = {"changed": True}
        del update_data["password"]

    for field, value in update_data.items():
        if field in old_values and old_values[field] != value:
            changes[field] = {"old": old_values[field], "new": value}
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    ip = get_client_ip(request)
    if changes:
        await log_audit(
            user=admin,
            action_type="user_update",
            action_target=user.username,
            action_summary=f"更新用户：{user.username}",
            detail={
                "target_user_id": str(user_id),
                "target_username": user.username,
                "changes": changes,
            },
            ip_address=ip,
            db=db,
        )

    return UserOut.model_validate(user)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    username = user.username
    display_name = user.display_name

    await db.delete(user)
    await db.flush()

    ip = get_client_ip(request)
    await log_audit(
        user=admin,
        action_type="user_delete",
        action_target=username,
        action_summary=f"删除用户：{username} ({display_name})",
        detail={
            "target_user_id": str(user_id),
            "target_username": username,
            "target_display_name": display_name,
            "target_role": user.role,
        },
        ip_address=ip,
        db=db,
    )

    return {"message": "删除成功"}


CACHE_SCOPES = {
    "dashboard": "dashboard:",
    "quotes": "quotes:",
    "bonds": "bonds:",
}


@router.get("/cache/scopes")
async def list_cache_scopes(_admin=Depends(require_admin)):
    return [
        {"key": "dashboard", "label": "看板数据 (overview, yield-curve, hot-bonds, alerts)"},
        {"key": "quotes", "label": "报价数据 (best, latest)"},
        {"key": "bonds", "label": "债券聚合行情 (aggregated, compare)"},
        {"key": "all", "label": "全部缓存"},
    ]


@router.post("/cache/refresh")
async def refresh_cache(
    request: Request,
    scope: Optional[str] = Query(
        None,
        description="缓存范围: dashboard / quotes / bonds / all，默认为 all",
    ),
    bond_id: Optional[str] = Query(None, description="刷新指定债券ID的聚合行情缓存"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    deleted = 0
    ip = get_client_ip(request)

    if bond_id:
        key = f"bonds:aggregated:{bond_id}"
        await CacheService.delete(key)
        await log_audit(
            user=admin,
            action_type="cache_refresh",
            action_target=f"bond:{bond_id}",
            action_summary=f"刷新债券 {bond_id} 的聚合行情缓存",
            detail={"scope": "bond", "bond_id": bond_id, "deleted_keys": 1},
            ip_address=ip,
            db=db,
        )
        return {"message": f"已刷新债券 {bond_id} 的聚合行情缓存", "deleted_keys": 1}

    actual_scope = scope or "all"
    if actual_scope == "all":
        deleted = await CacheService.clear_all()
    elif actual_scope in CACHE_SCOPES:
        prefix = CACHE_SCOPES[actual_scope]
        deleted = await CacheService.delete_by_prefix(prefix)
    else:
        raise HTTPException(status_code=400, detail=f"无效的缓存范围: {scope}，可选: dashboard, quotes, bonds, all")

    scope_label = {
        "dashboard": "看板数据",
        "quotes": "报价数据",
        "bonds": "债券聚合行情",
        "all": "全部缓存",
    }.get(actual_scope, actual_scope)

    await log_audit(
        user=admin,
        action_type="cache_refresh",
        action_target=actual_scope,
        action_summary=f"刷新缓存：{scope_label}",
        detail={"scope": actual_scope, "scope_label": scope_label, "deleted_keys": deleted},
        ip_address=ip,
        db=db,
    )

    return {"message": f"已刷新 {actual_scope} 范围的缓存", "deleted_keys": deleted}


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=200, description="每页数量"),
    user_id: Optional[UUID] = Query(None, description="用户ID筛选"),
    username: Optional[str] = Query(None, description="用户名模糊筛选"),
    action_type: Optional[str] = Query(None, description="动作类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))

    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)

    if username:
        query = query.where(AuditLog.username.ilike(f"%{username}%"))
        count_query = count_query.where(AuditLog.username.ilike(f"%{username}%"))

    if action_type:
        query = query.where(AuditLog.action_type == action_type)
        count_query = count_query.where(AuditLog.action_type == action_type)

    if start_date:
        query = query.where(AuditLog.created_at >= start_date)
        count_query = count_query.where(AuditLog.created_at >= start_date)

    if end_date:
        query = query.where(AuditLog.created_at <= end_date)
        count_query = count_query.where(AuditLog.created_at <= end_date)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        items=[AuditLogOut.model_validate(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/audit-logs/{log_id}", response_model=AuditLogOut)
async def get_audit_log_detail(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    return AuditLogOut.model_validate(log)


@router.get("/audit-action-types")
async def get_audit_action_types(_admin=Depends(require_admin)):
    return [{"key": a.key, "label": a.label} for a in AUDIT_ACTION_TYPES]
