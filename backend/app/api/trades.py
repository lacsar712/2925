from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond, MarketSource
from app.models.trade import Trade
from app.schemas.trade import TradeOut, TradeListOut, TradeStatistics
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/trades", tags=["成交"])


@router.get("/recent", response_model=TradeListOut)
async def get_recent_trades(
    source_type: Optional[str] = Query(None),
    bond_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = (
        select(Trade, MarketSource.name, MarketSource.source_type, Bond.code, Bond.name.label("bname"))
        .join(MarketSource, Trade.source_id == MarketSource.id)
        .join(Bond, Trade.bond_id == Bond.id)
    )
    count_query = select(func.count(Trade.id))

    if source_type:
        query = query.where(MarketSource.source_type == source_type)
        count_query = count_query.join(MarketSource, Trade.source_id == MarketSource.id).where(
            MarketSource.source_type == source_type
        )
    if bond_type:
        query = query.where(Bond.bond_type == bond_type)
        if source_type:
            count_query = count_query.join(Bond, Trade.bond_id == Bond.id).where(Bond.bond_type == bond_type)
        else:
            count_query = count_query.join(Bond, Trade.bond_id == Bond.id).where(Bond.bond_type == bond_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Trade.trade_time.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    rows = result.all()

    items = [
        TradeOut(
            **{c.key: getattr(t, c.key) for c in Trade.__table__.columns},
            source_name=sname,
            source_type=stype,
            bond_code=bcode,
            bond_name=bname,
        )
        for t, sname, stype, bcode, bname in rows
    ]

    return TradeListOut(items=items, total=total, page=page, page_size=page_size)


@router.get("/statistics", response_model=TradeStatistics)
async def get_trade_statistics(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    stats_result = await db.execute(
        select(
            func.sum(Trade.volume).label("total_vol"),
            func.sum(Trade.amount).label("total_amt"),
            func.count(Trade.id).label("cnt"),
            func.avg(Trade.price).label("avg_p"),
            func.avg(Trade.yield_rate).label("avg_y"),
        )
    )
    stats = stats_result.one()

    by_source_result = await db.execute(
        select(
            MarketSource.name,
            MarketSource.source_type,
            func.sum(Trade.volume).label("vol"),
            func.sum(Trade.amount).label("amt"),
            func.count(Trade.id).label("cnt"),
        )
        .join(MarketSource, Trade.source_id == MarketSource.id)
        .group_by(MarketSource.name, MarketSource.source_type)
    )

    by_type_result = await db.execute(
        select(
            Bond.bond_type,
            func.sum(Trade.volume).label("vol"),
            func.sum(Trade.amount).label("amt"),
            func.count(Trade.id).label("cnt"),
        )
        .join(Bond, Trade.bond_id == Bond.id)
        .group_by(Bond.bond_type)
    )

    return TradeStatistics(
        total_volume=float(stats.total_vol or 0),
        total_amount=float(stats.total_amt or 0),
        trade_count=stats.cnt or 0,
        avg_price=round(float(stats.avg_p), 4) if stats.avg_p else None,
        avg_yield=round(float(stats.avg_y), 4) if stats.avg_y else None,
        by_source=[
            {"name": r.name, "type": r.source_type, "volume": float(r.vol or 0),
             "amount": float(r.amt or 0), "count": r.cnt}
            for r in by_source_result.all()
        ],
        by_bond_type=[
            {"bond_type": r.bond_type, "volume": float(r.vol or 0),
             "amount": float(r.amt or 0), "count": r.cnt}
            for r in by_type_result.all()
        ],
    )
