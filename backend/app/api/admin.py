from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.bond import MarketSource
from app.models.user import User
from app.schemas.user import UserOut
from app.api.deps import require_admin
from app.services.cache_service import CacheService

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


CACHE_SCOPES = {
    "dashboard": "dashboard:",
    "quotes": "quotes:",
    "bonds": "bonds:",
}


@router.get("/cache/scopes")
async def list_cache_scopes(_admin=Depends(require_admin)):
    return [
        {"key": "dashboard", "label": "看板数据 (overview, yield-curve, hot-bonds, alerts)"},
        {"key": "quotes", "label": "报价数据 (best, latest)"},
        {"key": "bonds", "label": "债券聚合行情 (aggregated, compare)"},
        {"key": "all", "label": "全部缓存"},
    ]


@router.post("/cache/refresh")
async def refresh_cache(
    scope: Optional[str] = Query(
        None,
        description="缓存范围: dashboard / quotes / bonds / all，默认为 all",
    ),
    bond_id: Optional[str] = Query(None, description="刷新指定债券ID的聚合行情缓存"),
    _admin=Depends(require_admin),
):
    deleted = 0

    if bond_id:
        key = f"bonds:aggregated:{bond_id}"
        await CacheService.delete(key)
        return {"message": f"已刷新债券 {bond_id} 的聚合行情缓存", "deleted_keys": 1}

    if scope is None or scope == "all":
        deleted = await CacheService.clear_all()
        return {"message": "已刷新全部缓存", "deleted_keys": deleted}

    if scope not in CACHE_SCOPES:
        raise HTTPException(status_code=400, detail=f"无效的缓存范围: {scope}，可选: dashboard, quotes, bonds, all")

    prefix = CACHE_SCOPES[scope]
    deleted = await CacheService.delete_by_prefix(prefix)
    return {"message": f"已刷新 {scope} 范围的缓存", "deleted_keys": deleted}
