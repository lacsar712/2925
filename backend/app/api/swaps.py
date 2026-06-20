from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond
from app.models.swap import SwapQuote
from app.schemas.trade import SwapQuoteOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/swaps", tags=["收益互换"])


@router.get("", response_model=list[SwapQuoteOut])
async def get_swap_quotes(
    dealer: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = (
        select(SwapQuote, Bond.code, Bond.name.label("bname"))
        .join(Bond, SwapQuote.bond_id == Bond.id)
    )
    if dealer:
        query = query.where(SwapQuote.dealer.ilike(f"%{dealer}%"))
    query = query.order_by(SwapQuote.quote_time.desc())
    result = await db.execute(query)
    rows = result.all()

    return [
        SwapQuoteOut(
            **{c.key: getattr(sq, c.key) for c in SwapQuote.__table__.columns},
            bond_code=bcode,
            bond_name=bname,
        )
        for sq, bcode, bname in rows
    ]


@router.get("/bond/{bond_id}", response_model=list[SwapQuoteOut])
async def get_bond_swap_quotes(
    bond_id: UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(
        select(SwapQuote, Bond.code, Bond.name.label("bname"))
        .join(Bond, SwapQuote.bond_id == Bond.id)
        .where(SwapQuote.bond_id == bond_id)
        .order_by(SwapQuote.quote_time.desc())
    )
    rows = result.all()

    return [
        SwapQuoteOut(
            **{c.key: getattr(sq, c.key) for c in SwapQuote.__table__.columns},
            bond_code=bcode,
            bond_name=bname,
        )
        for sq, bcode, bname in rows
    ]
