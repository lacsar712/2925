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
from app.schemas.bond import BondOut, BondListOut, BondCalcRequest, BondCalcResponse
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


def _calculate_accrued_interest(
    face_value: float,
    coupon_rate: float,
    payment_frequency: int,
    settlement_date: date,
    maturity_date: date,
) -> tuple[float, int, date]:
    from dateutil.relativedelta import relativedelta

    coupon_per_period = (face_value * coupon_rate) / payment_frequency
    period_months = 12 // payment_frequency

    last_coupon_date = maturity_date
    while last_coupon_date > settlement_date:
        last_coupon_date -= relativedelta(months=period_months)

    next_coupon_date = last_coupon_date + relativedelta(months=period_months)

    days_in_period = (next_coupon_date - last_coupon_date).days
    days_since_last_coupon = (settlement_date - last_coupon_date).days

    accrued_interest = coupon_per_period * (days_since_last_coupon / days_in_period)
    return round(accrued_interest, 4), days_since_last_coupon, next_coupon_date


def _generate_cash_flows(
    face_value: float,
    coupon_rate: float,
    payment_frequency: int,
    settlement_date: date,
    maturity_date: date,
) -> list[dict]:
    from dateutil.relativedelta import relativedelta

    coupon_per_period = (face_value * coupon_rate) / payment_frequency
    period_months = 12 // payment_frequency

    cash_flows = []
    current_date = maturity_date

    while current_date > settlement_date:
        if current_date == maturity_date:
            cash_flows.append({
                "date": current_date.isoformat(),
                "coupon": round(coupon_per_period, 4),
                "principal": round(face_value, 4),
                "total": round(coupon_per_period + face_value, 4),
            })
        else:
            cash_flows.append({
                "date": current_date.isoformat(),
                "coupon": round(coupon_per_period, 4),
                "principal": 0,
                "total": round(coupon_per_period, 4),
            })
        current_date -= relativedelta(months=period_months)

    cash_flows.reverse()
    return cash_flows


def _calculate_dirty_price(
    cash_flows: list[dict],
    yield_rate: float,
    payment_frequency: int,
    settlement_date: date,
    days_since_last_coupon: int,
) -> tuple[float, float]:
    ytm_per_period = yield_rate / payment_frequency
    period_days = 365.25 / payment_frequency
    w = 1 - (days_since_last_coupon / period_days)

    dirty_price = 0
    macaulay_numerator = 0

    for i, cf in enumerate(cash_flows):
        t = w + i
        discount_factor = 1 / ((1 + ytm_per_period) ** t)
        pv = cf["total"] * discount_factor
        dirty_price += pv
        macaulay_numerator += (t / payment_frequency) * pv

    return round(dirty_price, 4), macaulay_numerator


def _calculate_ytm(
    cash_flows: list[dict],
    target_dirty_price: float,
    payment_frequency: int,
    settlement_date: date,
    days_since_last_coupon: int,
) -> float:
    def price_function(ytm):
        ytm_per_period = ytm / payment_frequency
        period_days = 365.25 / payment_frequency
        w = 1 - (days_since_last_coupon / period_days)
        price = 0
        for i, cf in enumerate(cash_flows):
            t = w + i
            price += cf["total"] / ((1 + ytm_per_period) ** t)
        return price - target_dirty_price

    def price_derivative(ytm):
        ytm_per_period = ytm / payment_frequency
        period_days = 365.25 / payment_frequency
        w = 1 - (days_since_last_coupon / period_days)
        derivative = 0
        for i, cf in enumerate(cash_flows):
            t = w + i
            derivative += -t * cf["total"] / (payment_frequency * ((1 + ytm_per_period) ** (t + 1)))
        return derivative

    ytm = 0.05
    for _ in range(100):
        f = price_function(ytm)
        if abs(f) < 1e-8:
            break
        df = price_derivative(ytm)
        if abs(df) < 1e-12:
            break
        ytm = ytm - f / df
        if ytm < -0.99:
            ytm = -0.99
        elif ytm > 10:
            ytm = 10

    return round(ytm, 6)


@router.post("/calculate", response_model=BondCalcResponse)
async def calculate_bond(
    request: BondCalcRequest,
    _user=Depends(get_current_user),
):
    from dateutil.relativedelta import relativedelta

    if request.settlement_date >= request.maturity_date:
        raise HTTPException(status_code=400, detail="结算日必须早于到期日")

    if request.face_value <= 0:
        raise HTTPException(status_code=400, detail="面值必须大于0")

    if request.coupon_rate < 0:
        raise HTTPException(status_code=400, detail="票息率不能为负")

    if request.payment_frequency not in [1, 2, 4, 12]:
        raise HTTPException(status_code=400, detail="付息频率必须是1、2、4或12")

    if request.clean_price is None and request.yield_rate is None:
        raise HTTPException(status_code=400, detail="必须指定净价或收益率中的至少一个")

    if request.clean_price is not None and request.yield_rate is not None:
        raise HTTPException(status_code=400, detail="不能同时指定净价和收益率")

    if request.clean_price is not None and request.clean_price <= 0:
        raise HTTPException(status_code=400, detail="净价必须大于0")

    if request.yield_rate is not None and request.yield_rate < -0.99:
        raise HTTPException(status_code=400, detail="收益率不能小于-99%")

    face_value = request.face_value
    coupon_rate = request.coupon_rate
    payment_frequency = request.payment_frequency
    settlement_date = request.settlement_date
    maturity_date = request.maturity_date

    accrued_interest, days_since_last_coupon, _ = _calculate_accrued_interest(
        face_value, coupon_rate, payment_frequency, settlement_date, maturity_date
    )

    cash_flows = _generate_cash_flows(
        face_value, coupon_rate, payment_frequency, settlement_date, maturity_date
    )

    years_to_maturity = (maturity_date - settlement_date).days / 365.25

    if request.clean_price is not None:
        clean_price = request.clean_price
        dirty_price = clean_price + accrued_interest
        yield_rate = _calculate_ytm(
            cash_flows, dirty_price, payment_frequency, settlement_date, days_since_last_coupon
        )
    else:
        yield_rate = request.yield_rate
        dirty_price, macaulay_numerator = _calculate_dirty_price(
            cash_flows, yield_rate, payment_frequency, settlement_date, days_since_last_coupon
        )
        clean_price = round(dirty_price - accrued_interest, 4)

    _, macaulay_numerator = _calculate_dirty_price(
        cash_flows, yield_rate, payment_frequency, settlement_date, days_since_last_coupon
    )

    if dirty_price > 0:
        macaulay_duration = round(macaulay_numerator / dirty_price, 4)
        modified_duration = round(macaulay_duration / (1 + yield_rate / payment_frequency), 4)
    else:
        macaulay_duration = 0
        modified_duration = 0

    return BondCalcResponse(
        face_value=face_value,
        coupon_rate=coupon_rate,
        payment_frequency=payment_frequency,
        settlement_date=settlement_date,
        maturity_date=maturity_date,
        clean_price=clean_price,
        yield_rate=yield_rate,
        accrued_interest=accrued_interest,
        dirty_price=dirty_price,
        macaulay_duration=macaulay_duration,
        modified_duration=modified_duration,
        years_to_maturity=round(years_to_maturity, 4),
        cash_flows=cash_flows,
    )
