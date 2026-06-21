import asyncio
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import async_session
from app.models.alert import PriceAlertRule, PriceAlertTrigger
from app.models.quote import Quote
from app.models.bond import Bond, MarketSource


def _get_mid_price(best_bid: float | None, best_ask: float | None) -> float | None:
    if best_bid is not None and best_ask is not None:
        return round((best_bid + best_ask) / 2, 6)
    if best_bid is not None:
        return best_bid
    if best_ask is not None:
        return best_ask
    return None


def _get_mid_yield(best_bid_yield: float | None, best_ask_yield: float | None) -> float | None:
    if best_bid_yield is not None and best_ask_yield is not None:
        return round((best_bid_yield + best_ask_yield) / 2, 6)
    if best_bid_yield is not None:
        return best_bid_yield
    if best_ask_yield is not None:
        return best_ask_yield
    return None


async def _get_aggregated_market_data(db: AsyncSession, bond_id: UUID) -> dict:
    result = await db.execute(
        select(
            func.max(Quote.bid_price).label("best_bid"),
            func.min(Quote.ask_price).label("best_ask"),
            func.max(Quote.bid_yield).label("best_bid_yield"),
            func.min(Quote.ask_yield).label("best_ask_yield"),
        )
        .join(MarketSource, Quote.source_id == MarketSource.id)
        .where(Quote.bond_id == bond_id, MarketSource.is_enabled == True)
    )
    row = result.one_or_none()
    if not row:
        return {"mid_price": None, "mid_yield": None}

    best_bid = float(row.best_bid) if row.best_bid is not None else None
    best_ask = float(row.best_ask) if row.best_ask is not None else None
    best_bid_yield = float(row.best_bid_yield) if row.best_bid_yield is not None else None
    best_ask_yield = float(row.best_ask_yield) if row.best_ask_yield is not None else None

    return {
        "mid_price": _get_mid_price(best_bid, best_ask),
        "mid_yield": _get_mid_yield(best_bid_yield, best_ask_yield),
        "best_bid": best_bid,
        "best_ask": best_ask,
        "best_bid_yield": best_bid_yield,
        "best_ask_yield": best_ask_yield,
    }


def _check_condition(condition: str, actual: float, threshold: float) -> bool:
    if condition == "above":
        return actual >= threshold
    elif condition == "below":
        return actual <= threshold
    return False


def _build_message(rule: PriceAlertRule, bond_code: str, bond_name: str, actual_value: float) -> str:
    type_label = "收益率" if rule.alert_type == "yield" else "净价"
    cond_label = "高于" if rule.condition == "above" else "低于"
    unit = "%" if rule.alert_type == "yield" else "元"
    return (
        f"[{bond_code} {bond_name}] {type_label}{cond_label}阈值："
        f"当前 {actual_value:.4f}{unit}，阈值 {float(rule.threshold):.4f}{unit}"
    )


async def process_alerts_once():
    try:
        async with async_session() as db:
            rules_result = await db.execute(
                select(PriceAlertRule, Bond.code, Bond.name)
                .join(Bond, PriceAlertRule.bond_id == Bond.id)
                .where(PriceAlertRule.is_enabled == True)
            )
            rules = rules_result.all()

            if not rules:
                return

            triggered_count = 0
            now = datetime.utcnow()

            for rule, bond_code, bond_name in rules:
                cooldown = timedelta(minutes=int(rule.trigger_cooldown_minutes))
                if rule.last_triggered_at and (now - rule.last_triggered_at) < cooldown:
                    continue

                market_data = await _get_aggregated_market_data(db, rule.bond_id)

                actual_value = None
                if rule.alert_type == "yield":
                    actual_value = market_data.get("mid_yield")
                elif rule.alert_type == "net_price":
                    actual_value = market_data.get("mid_price")

                if actual_value is None:
                    continue

                if _check_condition(rule.condition, actual_value, float(rule.threshold)):
                    message = _build_message(rule, bond_code, bond_name, actual_value)
                    trigger = PriceAlertTrigger(
                        rule_id=rule.id,
                        user_id=rule.user_id,
                        bond_id=rule.bond_id,
                        alert_type=rule.alert_type,
                        condition=rule.condition,
                        threshold=float(rule.threshold),
                        actual_value=actual_value,
                        is_read=False,
                        message=message,
                    )
                    db.add(trigger)
                    rule.last_triggered_at = now
                    triggered_count += 1

            if triggered_count > 0:
                await db.commit()
                logger.info(f"预警检测完成：触发 {triggered_count} 条告警")
    except Exception as e:
        logger.exception(f"预警检测服务异常：{e}")


async def alert_monitor_loop(interval_seconds: int = 10):
    logger.info(f"预警检测服务启动，检测间隔：{interval_seconds}秒")
    while True:
        try:
            await process_alerts_once()
        except Exception as e:
            logger.exception(f"预警检测循环异常：{e}")
        await asyncio.sleep(interval_seconds)
