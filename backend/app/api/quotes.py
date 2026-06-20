from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond, MarketSource
from app.models.quote import Quote
from app.schemas.quote import QuoteOut
from app.api.deps import get_current_user
from app.config import settings
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/quotes", tags=["报价"])


async def _cached_or_fetch(cache_key: str, cache_type: str, fetch_fn):
    if settings.CACHE_ENABLED:
        cached = await CacheService.get(cache_key)
        if cached:
            return {
                "data": cached["data"],
                "updated_at": cached["cached_at"],
            }
    data = await fetch_fn()
    if settings.CACHE_ENABLED:
        ttl = CacheService.get_ttl(cache_type)
        await CacheService.set(cache_key, data, ttl=ttl)
    from datetime import datetime
    return {
        "data": data,
        "updated_at": datetime.now().isoformat(),
    }


@router.get("/latest")
async def get_latest_quotes(
    source_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    async def _fetch():
        query = (
            select(Quote, MarketSource.name, MarketSource.source_type)
            .join(MarketSource, Quote.source_id == MarketSource.id)
        )
        if source_type:
            query = query.where(MarketSource.source_type == source_type)

        query = query.order_by(Quote.quote_time.desc()).limit(limit)
        result = await db.execute(query)
        rows = result.all()

        return [
            QuoteOut(
                **{c.key: getattr(q, c.key) for c in Quote.__table__.columns},
                source_name=sname,
                source_type=stype,
            ).model_dump()
            for q, sname, stype in rows
        ]

    cache_key = f"quotes:latest:{source_type or 'all'}:{limit}"
    return await _cached_or_fetch(cache_key, "quotes", _fetch)


@router.get("/best")
async def get_best_quotes(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    async def _fetch():
        subq = (
            select(
                Quote.bond_id,
                func.max(Quote.bid_price).label("best_bid"),
                func.min(Quote.ask_price).label("best_ask"),
                func.count(Quote.id).label("quote_count"),
            )
            .group_by(Quote.bond_id)
            .subquery()
        )

        result = await db.execute(
            select(Bond.id, Bond.code, Bond.name, Bond.bond_type, Bond.coupon_rate, Bond.remaining_term,
                   subq.c.best_bid, subq.c.best_ask, subq.c.quote_count)
            .join(subq, Bond.id == subq.c.bond_id)
            .order_by(subq.c.quote_count.desc())
            .limit(limit)
        )

        rows = result.all()
        return [
            {
                "bond_id": str(row.id),
                "code": row.code,
                "name": row.name,
                "bond_type": row.bond_type,
                "coupon_rate": float(row.coupon_rate) if row.coupon_rate else None,
                "remaining_term": float(row.remaining_term) if row.remaining_term else None,
                "best_bid": float(row.best_bid) if row.best_bid else None,
                "best_ask": float(row.best_ask) if row.best_ask else None,
                "spread": round(float(row.best_ask) - float(row.best_bid), 4) if row.best_ask and row.best_bid else None,
                "quote_count": row.quote_count,
            }
            for row in rows
        ]

    cache_key = f"quotes:best:{limit}"
    return await _cached_or_fetch(cache_key, "quotes", _fetch)
