import json
from datetime import datetime
from typing import Any, Optional
from loguru import logger
import redis.asyncio as redis

from app.config import settings


CACHE_NS = {
    "dashboard:overview": "dashboard",
    "dashboard:yield_curve": "dashboard",
    "dashboard:hot_bonds": "dashboard",
    "dashboard:alerts": "dashboard",
    "quotes:best": "quotes",
    "quotes:latest": "quotes",
    "bonds:aggregated": "bonds",
    "bonds:compare": "bonds",
}


class CacheService:
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return cls._client

    @classmethod
    async def close(cls):
        if cls._client:
            await cls._client.close()
            cls._client = None

    @classmethod
    def _wrap(cls, data: Any) -> str:
        payload = {
            "data": data,
            "cached_at": datetime.now().isoformat(),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)

    @classmethod
    def _unwrap(cls, raw: Optional[str]) -> Optional[dict]:
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    @classmethod
    async def get(cls, key: str) -> Optional[dict]:
        try:
            client = cls.get_client()
            raw = await client.get(key)
            return cls._unwrap(raw)
        except Exception as e:
            logger.warning(f"Redis get failed for key={key}: {e}")
            return None

    @classmethod
    async def set(cls, key: str, data: Any, ttl: Optional[int] = None) -> None:
        try:
            client = cls.get_client()
            value = cls._wrap(data)
            if ttl is not None:
                await client.setex(key, ttl, value)
            else:
                await client.set(key, value)
        except Exception as e:
            logger.warning(f"Redis set failed for key={key}: {e}")

    @classmethod
    async def delete(cls, key: str) -> None:
        try:
            client = cls.get_client()
            await client.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed for key={key}: {e}")

    @classmethod
    async def delete_by_prefix(cls, prefix: str) -> int:
        try:
            client = cls.get_client()
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=f"{prefix}*", count=200)
                if keys:
                    deleted += await client.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"Cleared cache prefix={prefix}, deleted={deleted} keys")
            return deleted
        except Exception as e:
            logger.warning(f"Redis delete_by_prefix failed for prefix={prefix}: {e}")
            return 0

    @classmethod
    async def clear_all(cls) -> int:
        try:
            client = cls.get_client()
            deleted = await client.flushdb()
            logger.info("Flushed entire Redis DB")
            return deleted if isinstance(deleted, int) else 0
        except Exception as e:
            logger.warning(f"Redis clear_all failed: {e}")
            return 0

    @classmethod
    def get_ttl(cls, cache_type: str) -> int:
        ttl_map = {
            "dashboard": settings.CACHE_DASHBOARD_TTL,
            "quotes": settings.CACHE_QUOTES_TTL,
            "bonds": settings.CACHE_BONDS_TTL,
        }
        return ttl_map.get(cache_type, settings.CACHE_DEFAULT_TTL)
