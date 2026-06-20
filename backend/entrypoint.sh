#!/bin/bash
set -e

echo "等待 PostgreSQL 启动..."
while ! python -c "import asyncio, asyncpg; asyncio.run(asyncpg.connect('postgresql://bondview:bondview123@db:5432/bondview'))" 2>/dev/null; do
    echo "PostgreSQL 尚未就绪，等待中..."
    sleep 2
done
echo "PostgreSQL 已就绪"

echo "等待 Redis 启动..."
while ! python -c "import redis; r=redis.Redis(host='redis', port=6379); r.ping()" 2>/dev/null; do
    echo "Redis 尚未就绪，等待中..."
    sleep 2
done
echo "Redis 已就绪"

echo "启动 BondView 后端服务..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
