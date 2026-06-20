from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import MarketSource
from app.models.user import User
from app.schemas.user import UserOut
from app.api.deps import require_admin

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
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    result = await db.execute(select(MarketSource).where(MarketSource.id == source_id))
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="行情源不存在")

    if "status" in body:
        source.status = body["status"]
    if "is_enabled" in body:
        source.is_enabled = body["is_enabled"]
    if "description" in body:
        source.description = body["description"]

    await db.flush()
    return {"message": "更新成功"}


@router.get("/users", response_model=list[UserOut])
async def get_users(db: AsyncSession = Depends(get_db), _admin=Depends(require_admin)):
    result = await db.execute(select(User).order_by(User.created_at))
    return [UserOut.model_validate(u) for u in result.scalars().all()]
