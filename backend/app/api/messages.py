from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.message import Message
from app.models.user import User
from app.schemas.message import (
    MessageOut,
    MessageListOut,
    UnreadCountByTypeOut,
    MessageCreate,
    MarkAllReadRequest,
    MessageLink,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/messages", tags=["消息中心"])

MESSAGE_TYPES = ("announcement", "market_movement", "price_alert", "admin_broadcast")


def _to_message_out(msg: Message) -> MessageOut:
    link = None
    if msg.link:
        link = MessageLink(**msg.link)
    return MessageOut(
        id=msg.id,
        type=msg.type,
        title=msg.title,
        content=msg.content,
        is_read=msg.is_read,
        link=link,
        metadata=msg.metadata_ or {},
        created_at=msg.created_at,
        updated_at=msg.updated_at,
    )


@router.get("/unread-count", response_model=UnreadCountByTypeOut)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    counts = {t: 0 for t in MESSAGE_TYPES}
    result = await db.execute(
        select(Message.type, func.count(Message.id))
        .where(Message.user_id == user.id, Message.is_read == False)
        .group_by(Message.type)
    )
    for msg_type, count in result.all():
        counts[msg_type] = count

    total = sum(counts.values())
    return UnreadCountByTypeOut(
        announcement=counts["announcement"],
        market_movement=counts["market_movement"],
        price_alert=counts["price_alert"],
        admin_broadcast=counts["admin_broadcast"],
        total=total,
    )


@router.get("/recent", response_model=list[MessageOut])
async def get_recent_messages(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message)
        .where(Message.user_id == user.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return [_to_message_out(m) for m in result.scalars().all()]


@router.post("/mark-read-all")
async def mark_all_read(
    body: MarkAllReadRequest = Body(default=MarkAllReadRequest()),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = update(Message).where(Message.user_id == user.id, Message.is_read == False)
    if body.type:
        stmt = stmt.where(Message.type == body.type)
    await db.execute(stmt.values(is_read=True))
    await db.commit()
    return {"success": True}


@router.get("", response_model=MessageListOut)
async def list_messages(
    type: Optional[str] = Query(None, description="消息类型"),
    is_read: Optional[bool] = Query(None, description="已读状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Message).where(Message.user_id == user.id)
    count_query = select(func.count(Message.id)).where(Message.user_id == user.id)

    if type:
        query = query.where(Message.type == type)
        count_query = count_query.where(Message.type == type)
    if is_read is not None:
        query = query.where(Message.is_read == is_read)
        count_query = count_query.where(Message.is_read == is_read)
    if start_time:
        query = query.where(Message.created_at >= start_time)
        count_query = count_query.where(Message.created_at >= start_time)
    if end_time:
        query = query.where(Message.created_at <= end_time)
        count_query = count_query.where(Message.created_at <= end_time)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Message.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessageListOut(
        items=[_to_message_out(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=MessageOut, status_code=201)
async def create_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.type == "admin_broadcast" and user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")

    target_user_ids: list[UUID]
    if data.user_id:
        if user.role != "admin" and data.user_id != user.id:
            raise HTTPException(status_code=403, detail="无权为其他用户创建消息")
        target_user_ids = [data.user_id]
    elif data.type == "admin_broadcast":
        users_result = await db.execute(select(User.id).where(User.is_active == True))
        target_user_ids = [row[0] for row in users_result.all()]
    else:
        target_user_ids = [user.id]

    link_data = data.link.model_dump() if data.link else None
    metadata = data.metadata or {}

    created: Message | None = None
    for uid in target_user_ids:
        msg = Message(
            user_id=uid,
            type=data.type,
            title=data.title,
            content=data.content,
            link=link_data,
            metadata_=metadata,
        )
        db.add(msg)
        if uid == user.id or (data.type == "admin_broadcast" and uid == target_user_ids[0]):
            created = msg

    await db.commit()
    if created:
        await db.refresh(created)
        return _to_message_out(created)

    first_result = await db.execute(
        select(Message)
        .where(Message.user_id == target_user_ids[0], Message.title == data.title)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    first = first_result.scalar_one()
    return _to_message_out(first)


@router.post("/{message_id}/mark-read")
async def mark_message_read(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    if not msg.is_read:
        msg.is_read = True
        await db.commit()
    return {"success": True}


@router.delete("/{message_id}")
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.user_id == user.id)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    await db.delete(msg)
    await db.commit()
    return {"success": True}
