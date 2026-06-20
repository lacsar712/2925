import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy import select, func

from app.database import async_session
from app.models.bond import Bond, MarketSource
from app.models.quote import Quote


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.subscriptions: dict[str, set[str]] = {}
        self.connection_subs: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> str:
        await websocket.accept()
        conn_id = str(uuid.uuid4())
        async with self._lock:
            self.active_connections[conn_id] = websocket
            self.connection_subs[conn_id] = set()
        logger.info(f"WebSocket 连接建立: {conn_id}")
        return conn_id

    async def disconnect(self, conn_id: str):
        async with self._lock:
            if conn_id in self.connection_subs:
                for bond_id in self.connection_subs[conn_id]:
                    if bond_id in self.subscriptions:
                        self.subscriptions[bond_id].discard(conn_id)
                        if not self.subscriptions[bond_id]:
                            del self.subscriptions[bond_id]
                del self.connection_subs[conn_id]
            if conn_id in self.active_connections:
                del self.active_connections[conn_id]
        logger.info(f"WebSocket 连接断开: {conn_id}")

    async def subscribe(self, conn_id: str, bond_id: str):
        async with self._lock:
            if conn_id not in self.connection_subs:
                return
            self.connection_subs[conn_id].add(bond_id)
            if bond_id not in self.subscriptions:
                self.subscriptions[bond_id] = set()
            self.subscriptions[bond_id].add(conn_id)
        logger.debug(f"连接 {conn_id} 订阅债券 {bond_id}")

    async def unsubscribe(self, conn_id: str, bond_id: str):
        async with self._lock:
            if conn_id in self.connection_subs:
                self.connection_subs[conn_id].discard(bond_id)
            if bond_id in self.subscriptions:
                self.subscriptions[bond_id].discard(conn_id)
                if not self.subscriptions[bond_id]:
                    del self.subscriptions[bond_id]
        logger.debug(f"连接 {conn_id} 取消订阅债券 {bond_id}")

    async def broadcast_bond_update(self, bond_id: str, message: dict):
        async with self._lock:
            connections = list(self.subscriptions.get(bond_id, set()))
            for conn_id in connections:
                ws = self.active_connections.get(conn_id)
                if ws:
                    try:
                        await ws.send_json(message)
                    except Exception as e:
                        logger.warning(f"发送消息失败 {conn_id}: {e}")

    async def send_personal(self, conn_id: str, message: dict):
        async with self._lock:
            ws = self.active_connections.get(conn_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"发送消息失败 {conn_id}: {e}")

    @property
    def subscribed_bond_ids(self) -> set[str]:
        return set(self.subscriptions.keys())


manager = ConnectionManager()


async def get_bond_aggregated_quote(bond_id: uuid.UUID) -> Optional[dict]:
    async with async_session() as db:
        bond_result = await db.execute(select(Bond).where(Bond.id == bond_id))
        bond = bond_result.scalar_one_or_none()
        if not bond:
            return None

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
            sources.append({
                "source_name": row.name,
                "source_type": row.source_type,
                "best_bid_price": float(row.best_bid) if row.best_bid else None,
                "best_ask_price": float(row.best_ask) if row.best_ask else None,
                "best_bid_yield": float(row.best_bid_yield) if row.best_bid_yield else None,
                "best_ask_yield": float(row.best_ask_yield) if row.best_ask_yield else None,
                "quote_count": row.cnt,
                "latest_quote_time": row.latest_time.isoformat() if row.latest_time else None,
            })
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

        return {
            "bond_id": str(bond.id),
            "code": bond.code,
            "name": bond.name,
            "sources": sources,
            "best_bid_price": global_best_bid,
            "best_ask_price": global_best_ask,
            "best_bid_yield": global_best_bid_yield,
            "best_ask_yield": global_best_ask_yield,
            "spread": spread,
            "total_quotes": total_quotes,
            "timestamp": datetime.now().isoformat(),
        }


async def quote_broadcast_loop(interval_seconds: int = 2):
    logger.info(f"行情推送服务启动，间隔 {interval_seconds}s")
    while True:
        try:
            bond_ids = manager.subscribed_bond_ids
            if bond_ids:
                for bond_id_str in bond_ids:
                    try:
                        bond_id = uuid.UUID(bond_id_str)
                        data = await get_bond_aggregated_quote(bond_id)
                        if data:
                            await manager.broadcast_bond_update(bond_id_str, {
                                "type": "quote_update",
                                "data": data,
                            })
                    except Exception as e:
                        logger.error(f"推送债券行情失败 {bond_id_str}: {e}")
        except Exception as e:
            logger.error(f"行情推送循环错误: {e}")
        await asyncio.sleep(interval_seconds)


async def handle_websocket(websocket: WebSocket):
    conn_id = await manager.connect(websocket)
    try:
        await manager.send_personal(conn_id, {
            "type": "connected",
            "data": {"conn_id": conn_id, "timestamp": datetime.now().isoformat()},
        })

        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                payload = message.get("data", {})

                if msg_type == "subscribe":
                    bond_ids = payload.get("bond_ids", [])
                    for bid in bond_ids:
                        await manager.subscribe(conn_id, bid)
                    await manager.send_personal(conn_id, {
                        "type": "subscribed",
                        "data": {"bond_ids": bond_ids},
                    })
                elif msg_type == "unsubscribe":
                    bond_ids = payload.get("bond_ids", [])
                    for bid in bond_ids:
                        await manager.unsubscribe(conn_id, bid)
                    await manager.send_personal(conn_id, {
                        "type": "unsubscribed",
                        "data": {"bond_ids": bond_ids},
                    })
                elif msg_type == "ping":
                    await manager.send_personal(conn_id, {
                        "type": "pong",
                        "data": {"timestamp": datetime.now().isoformat()},
                    })
                else:
                    await manager.send_personal(conn_id, {
                        "type": "error",
                        "data": {"message": f"未知消息类型: {msg_type}"},
                    })
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal(conn_id, {
                    "type": "error",
                    "data": {"message": "无效的 JSON 格式"},
                })
            except Exception as e:
                logger.error(f"处理 WebSocket 消息错误: {e}")
                await manager.send_personal(conn_id, {
                    "type": "error",
                    "data": {"message": str(e)},
                })
    finally:
        await manager.disconnect(conn_id)
