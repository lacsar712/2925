from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond, MarketSource
from app.models.quote import Quote
from app.models.trade import Trade
from app.schemas.bond import BondOut, BondListOut
from app.schemas.quote import QuoteOut, AggregatedQuoteOut, SourceQuoteSummary, BondBasic
from app.schemas.trade import TradeOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/bonds", tags=["债券"])


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


@router.get("/{bond_id}/aggregated", response_model=AggregatedQuoteOut)
async def get_aggregated_quotes(bond_id: UUID, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
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
        ))
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
    )
