from uuid import UUID
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond
from app.models.quote import Quote
from app.models.trade import Trade
from app.models.user import User, WatchlistGroup, WatchlistGroupBond
from app.schemas.watchlist import (
    WatchlistGroupCreate,
    WatchlistGroupUpdate,
    WatchlistGroupOut,
    WatchlistGroupDetailOut,
    WatchlistGroupBondWithData,
    WatchlistBondReorder,
)
from app.api.deps import get_current_user
from app.services.audit_service import log_audit, get_client_ip

router = APIRouter(prefix="/api/watchlist-groups", tags=["Watchlist分组"])


@router.get("", response_model=List[WatchlistGroupOut])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WatchlistGroup, func.count(WatchlistGroupBond.id).label("bond_count"))
        .outerjoin(WatchlistGroupBond, WatchlistGroup.id == WatchlistGroupBond.group_id)
        .where(WatchlistGroup.user_id == user.id)
        .group_by(WatchlistGroup.id)
        .order_by(WatchlistGroup.created_at.desc())
    )
    groups = []
    for row in result.all():
        g = row.WatchlistGroup
        groups.append(WatchlistGroupOut(
            id=g.id,
            name=g.name,
            bond_count=row.bond_count or 0,
            created_at=g.created_at,
            updated_at=g.updated_at,
        ))
    return groups


@router.post("", response_model=WatchlistGroupOut)
async def create_group(
    body: WatchlistGroupCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.user_id == user.id,
            WatchlistGroup.name == body.name.strip(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="分组名称已存在")

    group = WatchlistGroup(user_id=user.id, name=body.name.strip())
    db.add(group)
    await db.flush()

    ip = get_client_ip(request)
    await log_audit(
        user=user,
        action_type="watchlist_group_create",
        action_target=group.name,
        action_summary=f"创建分组：{group.name}",
        detail={"group_id": str(group.id), "group_name": group.name},
        ip_address=ip,
        db=db,
    )

    return WatchlistGroupOut(
        id=group.id,
        name=group.name,
        bond_count=0,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.put("/{group_id}", response_model=WatchlistGroupOut)
async def update_group(
    group_id: UUID,
    body: WatchlistGroupUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    old_name = group.name
    new_name = body.name.strip()

    if new_name != group.name:
        duplicate = await db.execute(
            select(WatchlistGroup).where(
                WatchlistGroup.user_id == user.id,
                WatchlistGroup.name == new_name,
                WatchlistGroup.id != group_id,
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="分组名称已存在")
        group.name = new_name

    await db.flush()

    ip = get_client_ip(request)
    if old_name != new_name:
        await log_audit(
            user=user,
            action_type="watchlist_group_update",
            action_target=new_name,
            action_summary=f"重命名分组：{old_name} → {new_name}",
            detail={
                "group_id": str(group_id),
                "old_name": old_name,
                "new_name": new_name,
            },
            ip_address=ip,
            db=db,
        )

    count_result = await db.execute(
        select(func.count(WatchlistGroupBond.id)).where(WatchlistGroupBond.group_id == group_id)
    )
    bond_count = count_result.scalar() or 0

    return WatchlistGroupOut(
        id=group.id,
        name=group.name,
        bond_count=bond_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete("/{group_id}")
async def delete_group(
    group_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    group_name = group.name

    await db.delete(group)
    await db.flush()

    ip = get_client_ip(request)
    await log_audit(
        user=user,
        action_type="watchlist_group_delete",
        action_target=group_name,
        action_summary=f"删除分组：{group_name}",
        detail={"group_id": str(group_id), "group_name": group_name},
        ip_address=ip,
        db=db,
    )

    return {"message": "分组已删除"}


@router.get("/{group_id}", response_model=WatchlistGroupDetailOut)
async def get_group_detail(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    bonds_result = await db.execute(
        select(WatchlistGroupBond, Bond)
        .join(Bond, WatchlistGroupBond.bond_id == Bond.id)
        .where(WatchlistGroupBond.group_id == group_id)
        .order_by(WatchlistGroupBond.order_index, WatchlistGroupBond.created_at)
    )
    bond_rows = bonds_result.all()

    seven_days_ago = datetime.now() - timedelta(days=7)
    bonds_with_data = []

    for gb, bond in bond_rows:
        quotes_result = await db.execute(
            select(
                func.max(Quote.bid_price).label("best_bid"),
                func.min(Quote.ask_price).label("best_ask"),
                func.max(Quote.bid_yield).label("best_bid_yield"),
                func.min(Quote.ask_yield).label("best_ask_yield"),
            )
            .where(Quote.bond_id == bond.id)
        )
        quote_row = quotes_result.first()

        best_bid = float(quote_row.best_bid) if quote_row and quote_row.best_bid else None
        best_ask = float(quote_row.best_ask) if quote_row and quote_row.best_ask else None
        best_bid_yield = float(quote_row.best_bid_yield) if quote_row and quote_row.best_bid_yield else None
        best_ask_yield = float(quote_row.best_ask_yield) if quote_row and quote_row.best_ask_yield else None

        spread = None
        if best_ask and best_bid:
            spread = round(best_ask - best_bid, 4)

        latest_trade_result = await db.execute(
            select(Trade.price, Trade.yield_rate)
            .where(Trade.bond_id == bond.id)
            .order_by(Trade.trade_time.desc())
            .limit(1)
        )
        latest_trade = latest_trade_result.first()
        latest_trade_price = float(latest_trade.price) if latest_trade else None
        latest_trade_yield = float(latest_trade.yield_rate) if latest_trade and latest_trade.yield_rate else None

        volume_7d_result = await db.execute(
            select(func.sum(Trade.volume))
            .where(
                and_(
                    Trade.bond_id == bond.id,
                    Trade.trade_time >= seven_days_ago,
                )
            )
        )
        volume_7d = float(volume_7d_result.scalar() or 0)

        bonds_with_data.append(WatchlistGroupBondWithData(
            id=bond.id,
            code=bond.code,
            name=bond.name,
            bond_type=bond.bond_type,
            issuer=bond.issuer,
            coupon_rate=float(bond.coupon_rate) if bond.coupon_rate else None,
            remaining_term=float(bond.remaining_term) if bond.remaining_term else None,
            credit_rating=bond.credit_rating,
            best_bid_price=best_bid,
            best_ask_price=best_ask,
            best_bid_yield=best_bid_yield,
            best_ask_yield=best_ask_yield,
            latest_trade_price=latest_trade_price,
            latest_trade_yield=latest_trade_yield,
            spread=spread,
            volume_7d=volume_7d,
            order_index=gb.order_index,
        ))

    return WatchlistGroupDetailOut(
        id=group.id,
        name=group.name,
        bonds=bonds_with_data,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.post("/{group_id}/bonds/{bond_id}")
async def add_bond_to_group(
    group_id: UUID,
    bond_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group_result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")

    bond_result = await db.execute(select(Bond).where(Bond.id == bond_id))
    if not bond_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="债券不存在")

    existing = await db.execute(
        select(WatchlistGroupBond).where(
            WatchlistGroupBond.group_id == group_id,
            WatchlistGroupBond.bond_id == bond_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该债券已在分组中")

    max_index_result = await db.execute(
        select(func.max(WatchlistGroupBond.order_index)).where(WatchlistGroupBond.group_id == group_id)
    )
    max_index = max_index_result.scalar() or -1

    gb = WatchlistGroupBond(
        group_id=group_id,
        bond_id=bond_id,
        order_index=max_index + 1,
    )
    db.add(gb)
    await db.flush()
    return {"message": "已添加到分组"}


@router.delete("/{group_id}/bonds/{bond_id}")
async def remove_bond_from_group(
    group_id: UUID,
    bond_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group_result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="分组不存在")

    result = await db.execute(
        delete(WatchlistGroupBond).where(
            WatchlistGroupBond.group_id == group_id,
            WatchlistGroupBond.bond_id == bond_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="该债券不在分组中")
    await db.flush()
    return {"message": "已从分组移除"}


@router.put("/{group_id}/bonds/reorder")
async def reorder_bonds(
    group_id: UUID,
    body: WatchlistBondReorder,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    group_result = await db.execute(
        select(WatchlistGroup).where(
            WatchlistGroup.id == group_id,
            WatchlistGroup.user_id == user.id,
        )
    )
    if not group_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="分组不存在")

    for idx, bid in enumerate(body.bond_ids):
        gb_result = await db.execute(
            select(WatchlistGroupBond).where(
                WatchlistGroupBond.group_id == group_id,
                WatchlistGroupBond.bond_id == bid,
            )
        )
        gb = gb_result.scalar_one_or_none()
        if gb:
            gb.order_index = idx

    await db.flush()
    return {"message": "排序已更新"}
