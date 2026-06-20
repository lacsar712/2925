from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.database import init_db, async_session
from app.seed.seed_data import seed_all
from app.api import auth, bonds, quotes, trades, futures, swaps, dashboard, favorites, admin

logger.remove()
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("BondView 债券行情聚合系统启动中...")
    await init_db()
    logger.info("数据库表创建完成")

    async with async_session() as session:
        await seed_all(session)

    logger.info("系统启动完成")
    yield
    logger.info("系统关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="债券行情聚合系统 - 多源行情整合展示平台",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bonds.router)
app.include_router(quotes.router)
app.include_router(trades.router)
app.include_router(futures.router)
app.include_router(swaps.router)
app.include_router(dashboard.router)
app.include_router(favorites.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}
