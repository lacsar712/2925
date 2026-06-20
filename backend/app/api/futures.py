from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.futures import FuturesQuote
from app.schemas.trade import FuturesQuoteOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/futures", tags=["国债期货"])


@router.get("/contracts", response_model=list[FuturesQuoteOut])
async def get_futures_contracts(
    contract_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    query = select(FuturesQuote)
    if contract_type:
        query = query.where(FuturesQuote.contract_type == contract_type)
    query = query.order_by(FuturesQuote.contract_code)
    result = await db.execute(query)
    return [FuturesQuoteOut.model_validate(f) for f in result.scalars().all()]


@router.get("/basis", response_model=list[dict])
async def get_basis_analysis(db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(
        select(FuturesQuote)
        .where(FuturesQuote.basis.isnot(None))
        .order_by(FuturesQuote.contract_code)
    )
    futures = result.scalars().all()
    return [
        {
            "contract_code": f.contract_code,
            "contract_type": f.contract_type,
            "latest_price": float(f.latest_price),
            "basis": float(f.basis) if f.basis else None,
            "volume": f.volume,
            "open_interest": f.open_interest,
        }
        for f in futures
    ]


@router.get("/{code}", response_model=FuturesQuoteOut)
async def get_futures_detail(code: str, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    result = await db.execute(select(FuturesQuote).where(FuturesQuote.contract_code == code))
    fq = result.scalar_one_or_none()
    if not fq:
        raise HTTPException(status_code=404, detail="合约不存在")
    return FuturesQuoteOut.model_validate(fq)
