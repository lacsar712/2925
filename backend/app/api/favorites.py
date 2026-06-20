from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import Bond
from app.models.user import User, UserFavorite
from app.schemas.bond import BondOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["收藏"])


@router.get("", response_model=list[BondOut])
async def get_favorites(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Bond)
        .join(UserFavorite, Bond.id == UserFavorite.bond_id)
        .where(UserFavorite.user_id == user.id)
        .order_by(UserFavorite.created_at.desc())
    )
    return [BondOut.model_validate(b) for b in result.scalars().all()]


@router.post("/{bond_id}")
async def add_favorite(
    bond_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.bond_id == bond_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已收藏该债券")

    bond = await db.execute(select(Bond).where(Bond.id == bond_id))
    if not bond.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="债券不存在")

    fav = UserFavorite(user_id=user.id, bond_id=bond_id)
    db.add(fav)
    await db.flush()
    return {"message": "收藏成功"}


@router.delete("/{bond_id}")
async def remove_favorite(
    bond_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        delete(UserFavorite).where(
            UserFavorite.user_id == user.id,
            UserFavorite.bond_id == bond_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="未找到收藏记录")
    return {"message": "取消收藏成功"}
