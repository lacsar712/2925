from typing import Optional, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import async_session
from app.models.audit import AuditLog
from app.models.user import User


async def log_audit(
    user: Optional[User] = None,
    username: Optional[str] = None,
    action_type: str = "",
    action_target: Optional[str] = None,
    action_summary: str = "",
    detail: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    db: Optional[AsyncSession] = None,
) -> Optional[AuditLog]:
    if not action_type or not action_summary:
        logger.warning("审计日志记录失败：缺少 action_type 或 action_summary")
        return None

    user_id = None
    uname = username or "unknown"

    if user:
        user_id = user.id
        uname = user.username

    audit_log = AuditLog(
        user_id=user_id,
        username=uname,
        action_type=action_type,
        action_target=action_target,
        action_summary=action_summary,
        detail=detail,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    if db:
        db.add(audit_log)
        await db.flush()
        return audit_log

    try:
        async with async_session() as session:
            session.add(audit_log)
            await session.commit()
            return audit_log
    except Exception as e:
        logger.error(f"审计日志写入数据库失败: {e}")
        return None


def get_client_ip(request) -> Optional[str]:
    if not request:
        return None
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("x-real-ip")
    if x_real_ip:
        return x_real_ip
    try:
        return request.client.host if request.client else None
    except Exception:
        return None


def get_user_agent(request) -> Optional[str]:
    if not request:
        return None
    return request.headers.get("user-agent")
