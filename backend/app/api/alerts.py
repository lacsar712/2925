from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy import select, func, delete, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond
from app.models.user import User
from app.models.alert import PriceAlertRule, PriceAlertTrigger
from app.schemas.alert import (
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleOut,
    AlertRuleListOut,
    AlertRuleToggleOut,
    AlertTriggerOut,
    AlertTriggerListOut,
    UnreadCountOut,
    MarkReadRequest,
)
from app.api.deps import get_current_user
from app.services.audit_service import log_audit, get_client_ip

router = APIRouter(prefix="/api/alerts", tags=["价格预警"])


@router.get("/rules", response_model=AlertRuleListOut)
async def list_alert_rules(
    bond_id: Optional[UUID] = Query(None, description="按债券筛选"),
    is_enabled: Optional[bool] = Query(None, description="按启用状态筛选"),
    alert_type: Optional[str] = Query(None, description="预警类型：yield/net_price"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(PriceAlertRule).where(PriceAlertRule.user_id == user.id)
    count_query = select(func.count(PriceAlertRule.id)).where(PriceAlertRule.user_id == user.id)

    if bond_id:
        query = query.where(PriceAlertRule.bond_id == bond_id)
        count_query = count_query.where(PriceAlertRule.bond_id == bond_id)
    if is_enabled is not None:
        query = query.where(PriceAlertRule.is_enabled == is_enabled)
        count_query = count_query.where(PriceAlertRule.is_enabled == is_enabled)
    if alert_type:
        query = query.where(PriceAlertRule.alert_type == alert_type)
        count_query = count_query.where(PriceAlertRule.alert_type == alert_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(PriceAlertRule.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rules = result.scalars().all()

    return AlertRuleListOut(
        items=[AlertRuleOut.model_validate(r) for r in rules],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/rules/{rule_id}", response_model=AlertRuleOut)
async def get_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertRule).where(
            PriceAlertRule.id == rule_id,
            PriceAlertRule.user_id == user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="预警规则不存在")
    return AlertRuleOut.model_validate(rule)


@router.post("/rules", response_model=AlertRuleOut, status_code=201)
async def create_alert_rule(
    data: AlertRuleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bond_result = await db.execute(select(Bond).where(Bond.id == data.bond_id))
    bond = bond_result.scalar_one_or_none()
    if not bond:
        raise HTTPException(status_code=404, detail="债券不存在")

    existing = await db.execute(
        select(PriceAlertRule).where(
            PriceAlertRule.user_id == user.id,
            PriceAlertRule.bond_id == data.bond_id,
            PriceAlertRule.alert_type == data.alert_type,
            PriceAlertRule.condition == data.condition,
            PriceAlertRule.threshold == data.threshold,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="相同的预警规则已存在")

    rule = PriceAlertRule(
        user_id=user.id,
        bond_id=data.bond_id,
        alert_type=data.alert_type,
        condition=data.condition,
        threshold=data.threshold,
        is_enabled=data.is_enabled if data.is_enabled is not None else True,
        trigger_cooldown_minutes=data.trigger_cooldown_minutes or 5,
        description=data.description,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule)

    ip = get_client_ip(request)
    alert_type_label = "收益率" if data.alert_type == "yield" else "净价"
    condition_label = "高于" if data.condition == "above" else "低于"
    await log_audit(
        user=user,
        action_type="alert_rule_create",
        action_target=bond.name or str(data.bond_id),
        action_summary=f"创建预警规则：{bond.name} {alert_type_label} {condition_label} {data.threshold}",
        detail={
            "rule_id": str(rule.id),
            "bond_id": str(data.bond_id),
            "bond_name": bond.name,
            "bond_code": bond.code,
            "alert_type": data.alert_type,
            "condition": data.condition,
            "threshold": float(data.threshold),
            "is_enabled": rule.is_enabled,
        },
        ip_address=ip,
        db=db,
    )

    return AlertRuleOut.model_validate(rule)


@router.put("/rules/{rule_id}", response_model=AlertRuleOut)
async def update_alert_rule(
    rule_id: UUID,
    data: AlertRuleUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertRule, Bond)
        .join(Bond, PriceAlertRule.bond_id == Bond.id)
        .where(
            PriceAlertRule.id == rule_id,
            PriceAlertRule.user_id == user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="预警规则不存在")

    rule, bond = row
    old_values = {
        "alert_type": rule.alert_type,
        "condition": rule.condition,
        "threshold": float(rule.threshold),
        "is_enabled": rule.is_enabled,
        "description": rule.description,
    }

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.flush()
    await db.refresh(rule)

    ip = get_client_ip(request)
    changes = {}
    for k, v in update_data.items():
        if k in old_values and old_values[k] != v:
            if k == "threshold":
                changes[k] = {"old": old_values[k], "new": float(v)}
            else:
                changes[k] = {"old": old_values[k], "new": v}

    if changes:
        alert_type_label = "收益率" if rule.alert_type == "yield" else "净价"
        await log_audit(
            user=user,
            action_type="alert_rule_update",
            action_target=bond.name or str(rule.bond_id),
            action_summary=f"更新预警规则：{bond.name} {alert_type_label}",
            detail={
                "rule_id": str(rule_id),
                "bond_id": str(rule.bond_id),
                "bond_name": bond.name,
                "bond_code": bond.code,
                "changes": changes,
            },
            ip_address=ip,
            db=db,
        )

    return AlertRuleOut.model_validate(rule)


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertRule, Bond)
        .join(Bond, PriceAlertRule.bond_id == Bond.id)
        .where(
            PriceAlertRule.id == rule_id,
            PriceAlertRule.user_id == user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="预警规则不存在")

    rule, bond = row
    alert_type_label = "收益率" if rule.alert_type == "yield" else "净价"
    condition_label = "高于" if rule.condition == "above" else "低于"

    await db.delete(rule)

    ip = get_client_ip(request)
    await log_audit(
        user=user,
        action_type="alert_rule_delete",
        action_target=bond.name or str(rule.bond_id),
        action_summary=f"删除预警规则：{bond.name} {alert_type_label} {condition_label} {float(rule.threshold)}",
        detail={
            "rule_id": str(rule_id),
            "bond_id": str(rule.bond_id),
            "bond_name": bond.name,
            "bond_code": bond.code,
            "alert_type": rule.alert_type,
            "condition": rule.condition,
            "threshold": float(rule.threshold),
        },
        ip_address=ip,
        db=db,
    )

    return {"message": "删除成功"}


@router.post("/rules/{rule_id}/toggle", response_model=AlertRuleToggleOut)
async def toggle_alert_rule(
    rule_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertRule, Bond)
        .join(Bond, PriceAlertRule.bond_id == Bond.id)
        .where(
            PriceAlertRule.id == rule_id,
            PriceAlertRule.user_id == user.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="预警规则不存在")

    rule, bond = row
    old_enabled = rule.is_enabled
    rule.is_enabled = not rule.is_enabled
    await db.flush()

    ip = get_client_ip(request)
    action_type = "alert_rule_update"
    action_label = "启用" if rule.is_enabled else "停用"
    alert_type_label = "收益率" if rule.alert_type == "yield" else "净价"
    await log_audit(
        user=user,
        action_type=action_type,
        action_target=bond.name or str(rule.bond_id),
        action_summary=f"{action_label}预警规则：{bond.name} {alert_type_label}",
        detail={
            "rule_id": str(rule_id),
            "bond_id": str(rule.bond_id),
            "bond_name": bond.name,
            "bond_code": bond.code,
            "is_enabled": {"old": old_enabled, "new": rule.is_enabled},
        },
        ip_address=ip,
        db=db,
    )

    return AlertRuleToggleOut(
        id=rule.id,
        is_enabled=rule.is_enabled,
        message=f"已{'启用' if rule.is_enabled else '停用'}预警规则",
    )


@router.get("/triggers", response_model=AlertTriggerListOut)
async def list_alert_triggers(
    bond_id: Optional[UUID] = Query(None, description="按债券筛选"),
    is_read: Optional[bool] = Query(None, description="按已读状态筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(PriceAlertTrigger).where(PriceAlertTrigger.user_id == user.id)
    count_query = select(func.count(PriceAlertTrigger.id)).where(PriceAlertTrigger.user_id == user.id)

    if bond_id:
        query = query.where(PriceAlertTrigger.bond_id == bond_id)
        count_query = count_query.where(PriceAlertTrigger.bond_id == bond_id)
    if is_read is not None:
        query = query.where(PriceAlertTrigger.is_read == is_read)
        count_query = count_query.where(PriceAlertTrigger.is_read == is_read)
    if start_time:
        query = query.where(PriceAlertTrigger.created_at >= start_time)
        count_query = count_query.where(PriceAlertTrigger.created_at >= start_time)
    if end_time:
        query = query.where(PriceAlertTrigger.created_at <= end_time)
        count_query = count_query.where(PriceAlertTrigger.created_at <= end_time)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(PriceAlertTrigger.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    triggers = result.scalars().all()

    return AlertTriggerListOut(
        items=[AlertTriggerOut.model_validate(t) for t in triggers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/triggers/recent", response_model=list[AlertTriggerOut])
async def get_recent_triggers(
    limit: int = Query(20, ge=1, le=100, description="返回最近N条"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertTrigger)
        .where(PriceAlertTrigger.user_id == user.id)
        .order_by(PriceAlertTrigger.created_at.desc())
        .limit(limit)
    )
    triggers = result.scalars().all()
    return [AlertTriggerOut.model_validate(t) for t in triggers]


@router.get("/unread-count", response_model=UnreadCountOut)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count(PriceAlertTrigger.id)).where(
            PriceAlertTrigger.user_id == user.id,
            PriceAlertTrigger.is_read == False,
        )
    )
    count = result.scalar() or 0
    return UnreadCountOut(count=count)


@router.post("/triggers/mark-read")
async def mark_triggers_read(
    data: MarkReadRequest = Body(default_factory=MarkReadRequest),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.trigger_ids and len(data.trigger_ids) > 0:
        await db.execute(
            update(PriceAlertTrigger)
            .where(
                PriceAlertTrigger.user_id == user.id,
                PriceAlertTrigger.id.in_(data.trigger_ids),
                PriceAlertTrigger.is_read == False,
            )
            .values(is_read=True)
        )
    else:
        await db.execute(
            update(PriceAlertTrigger)
            .where(
                PriceAlertTrigger.user_id == user.id,
                PriceAlertTrigger.is_read == False,
            )
            .values(is_read=True)
        )
    return {"message": "标记已读成功"}


@router.post("/triggers/{trigger_id}/mark-read")
async def mark_single_trigger_read(
    trigger_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(PriceAlertTrigger).where(
            PriceAlertTrigger.id == trigger_id,
            PriceAlertTrigger.user_id == user.id,
        )
    )
    trigger = result.scalar_one_or_none()
    if not trigger:
        raise HTTPException(status_code=404, detail="触发记录不存在")

    trigger.is_read = True
    await db.flush()
    return {"message": "标记已读成功"}
