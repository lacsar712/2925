from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond, MarketSource
from app.models.quote import Quote
from app.models.trade import Trade
from app.schemas.bond import BondOut, BondListOut
from app.schemas.quote import QuoteOut, AggregatedQuoteOut, SourceQuoteSummary, BondBasic, BondCompareData, BondCompareResponse
from app.schemas.trade import TradeOut
from app.api.deps import get_current_user
from app.config import settings
from app.services.cache_service import CacheService

router = APIRouter(prefix="/api/bonds", tags=["债券"])


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
    from datetime import datetime as _dt
    return {
        "data": data,
        "updated_at": _dt.now().isoformat(),
    }


@router.get("", response_model=BondListOut)
async def list_bonds(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    bond_type: Optional[str] = Query(None, description="债券类型"),
    credit_rating: Optional[str] = Query(None, description="信用评级"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = select(Bond)
    count_query = select(func.count(Bond.id))

    if keyword:
        kw = f"%{keyword}%"
        filter_cond = or_(Bond.code.ilike(kw), Bond.name.ilike(kw), Bond.issuer.ilike(kw))
        query = query.where(filter_cond)
        count_query = count_query.where(filter_cond)

    if bond_type:
        query = query.where(Bond.bond_type == bond_type)
        count_query = count_query.where(Bond.bond_type == bond_type)

    if credit_rating:
        query = query.where(Bond.credit_rating == credit_rating)
        count_query = count_query.where(Bond.credit_rating == credit_rating)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Bond.code).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    bonds = result.scalars().all()

    return BondListOut(
        items=[BondOut.model_validate(b) for b in bonds],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{bond_id}", response_model=BondOut)
async def get_bond(bond_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(Bond).where(Bond.id == bond_id))
    bond = result.scalar_one_or_none()
    if not bond:
        raise HTTPException(status_code=404, detail="债券不存在")
    return BondOut.model_validate(bond)


@router.get("/{bond_id}/quotes", response_model=list[QuoteOut])
async def get_bond_quotes(bond_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(
        select(Quote, MarketSource.name, MarketSource.source_type)
        .join(MarketSource, Quote.source_id == MarketSource.id)
        .where(Quote.bond_id == bond_id)
        .order_by(Quote.quote_time.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        QuoteOut(
            **{c.key: getattr(q, c.key) for c in Quote.__table__.columns},
            source_name=sname,
            source_type=stype,
        )
        for q, sname, stype in rows
    ]


@router.get("/{bond_id}/trades", response_model=list[TradeOut])
async def get_bond_trades(bond_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(
        select(Trade, MarketSource.name, MarketSource.source_type, Bond.code, Bond.name.label("bname"))
        .join(MarketSource, Trade.source_id == MarketSource.id)
        .join(Bond, Trade.bond_id == Bond.id)
        .where(Trade.bond_id == bond_id)
        .order_by(Trade.trade_time.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        TradeOut(
            **{c.key: getattr(t, c.key) for c in Trade.__table__.columns},
            source_name=sname,
            source_type=stype,
            bond_code=bcode,
            bond_name=bname,
        )
        for t, sname, stype, bcode, bname in rows
    ]


@router.get("/{bond_id}/aggregated")
async def get_aggregated_quotes(bond_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    async def _fetch():
        bond_result = await db.execute(select(Bond).where(Bond.id == bond_id))
        bond = bond_result.scalar_one_or_none()
        if not bond:
            raise HTTPException(status_code=404, detail="债券不存在")

        quotes_result = await db.execute(
            select(
                MarketSource.name,
                MarketSource.source_type,
                func.max(Quote.bid_price).label("best_bid"),
                func.min(Quote.ask_price).label("best_ask"),
                func.max(Quote.bid_yield).label("best_bid_yield"),
                func.min(Quote.ask_yield).label("best_ask_yield"),
                func.count(Quote.id).label("cnt"),
                func.max(Quote.quote_time).label("latest_time"),
            )
            .join(MarketSource, Quote.source_id == MarketSource.id)
            .where(Quote.bond_id == bond_id)
            .group_by(MarketSource.name, MarketSource.source_type)
        )
        source_rows = quotes_result.all()

        sources = []
        global_best_bid = None
        global_best_ask = None
        global_best_bid_yield = None
        global_best_ask_yield = None
        total_quotes = 0

        for row in source_rows:
            sources.append(SourceQuoteSummary(
                source_name=row.name,
                source_type=row.source_type,
                best_bid_price=float(row.best_bid) if row.best_bid else None,
                best_ask_price=float(row.best_ask) if row.best_ask else None,
                best_bid_yield=float(row.best_bid_yield) if row.best_bid_yield else None,
                best_ask_yield=float(row.best_ask_yield) if row.best_ask_yield else None,
                quote_count=row.cnt,
                latest_quote_time=row.latest_time,
            ).model_dump())
            total_quotes += row.cnt

            if row.best_bid and (global_best_bid is None or float(row.best_bid) > global_best_bid):
                global_best_bid = float(row.best_bid)
            if row.best_ask and (global_best_ask is None or float(row.best_ask) < global_best_ask):
                global_best_ask = float(row.best_ask)
            if row.best_bid_yield and (global_best_bid_yield is None or float(row.best_bid_yield) > global_best_bid_yield):
                global_best_bid_yield = float(row.best_bid_yield)
            if row.best_ask_yield and (global_best_ask_yield is None or float(row.best_ask_yield) < global_best_ask_yield):
                global_best_ask_yield = float(row.best_ask_yield)

        spread = None
        if global_best_ask and global_best_bid:
            spread = round(global_best_ask - global_best_bid, 4)

        return AggregatedQuoteOut(
            bond=BondBasic.model_validate(bond),
            sources=sources,
            best_bid_price=global_best_bid,
            best_ask_price=global_best_ask,
            best_bid_yield=global_best_bid_yield,
            best_ask_yield=global_best_ask_yield,
            spread=spread,
            total_quotes=total_quotes,
        ).model_dump()

    cache_key = f"bonds:aggregated:{bond_id}"
    return await _cached_or_fetch(cache_key, "bonds", _fetch)


@router.get("/compare/batch")
async def get_bonds_compare(
    bond_ids: str = Query(..., description="债券ID列表，逗号分隔"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    id_list = [UUID(id_str.strip()) for id_str in bond_ids.split(",") if id_str.strip()]
    if len(id_list) == 0:
        raise HTTPException(status_code=400, detail="请提供至少一个债券ID")
    if len(id_list) > 4:
        raise HTTPException(status_code=400, detail="最多只能对比4只债券")

    cache_key_suffix = "_".join(sorted([str(i) for i in id_list]))

    async def _fetch():
        seven_days_ago = datetime.now() - timedelta(days=7)

        result = []
        for bond_id in id_list:
            bond_result = await db.execute(select(Bond).where(Bond.id == bond_id))
            bond = bond_result.scalar_one_or_none()
            if not bond:
                continue

            quotes_result = await db.execute(
                select(
                    func.max(Quote.bid_price).label("best_bid"),
                    func.min(Quote.ask_price).label("best_ask"),
                    func.max(Quote.bid_yield).label("best_bid_yield"),
                    func.min(Quote.ask_yield).label("best_ask_yield"),
                )
                .where(Quote.bond_id == bond_id)
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
                .where(Trade.bond_id == bond_id)
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
                        Trade.bond_id == bond_id,
                        Trade.trade_time >= seven_days_ago,
                    )
                )
            )
            volume_7d = float(volume_7d_result.scalar() or 0)

            result.append(BondCompareData(
                id=bond.id,
                code=bond.code,
                name=bond.name,
                bond_type=bond.bond_type,
                credit_rating=bond.credit_rating,
                remaining_term=float(bond.remaining_term) if bond.remaining_term else None,
                coupon_rate=float(bond.coupon_rate) if bond.coupon_rate else None,
                best_bid_price=best_bid,
                best_ask_price=best_ask,
                best_bid_yield=best_bid_yield,
                best_ask_yield=best_ask_yield,
                latest_trade_price=latest_trade_price,
                latest_trade_yield=latest_trade_yield,
                volume_7d=volume_7d,
                spread=spread,
            ).model_dump())

        return BondCompareResponse(items=result).model_dump()

    cache_key = f"bonds:compare:{cache_key_suffix}"
    return await _cached_or_fetch(cache_key, "bonds", _fetch)
