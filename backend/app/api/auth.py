from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserOut
from app.api.deps import get_current_user
from app.services.audit_service import log_audit, get_client_ip, get_user_agent

router = APIRouter(prefix="/api/auth", tags=["认证"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    ip = get_client_ip(request)
    ua = get_user_agent(request)

    if not user or not pwd_context.verify(body.password, user.password_hash):
        await log_audit(
            username=body.username,
            action_type="user_login_failed",
            action_summary=f"用户 {body.username} 登录失败：用户名或密码错误",
            detail={"username": body.username, "reason": "invalid_credentials"},
            ip_address=ip,
            user_agent=ua,
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if not user.is_active:
        await log_audit(
            username=body.username,
            action_type="user_login_failed",
            action_summary=f"用户 {body.username} 登录失败：账号已禁用",
            detail={"username": body.username, "reason": "account_disabled"},
            ip_address=ip,
            user_agent=ua,
            db=db,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    token = create_access_token(str(user.id))

    await log_audit(
        user=user,
        action_type="user_login",
        action_summary=f"用户 {user.username} 登录成功",
        detail={"username": user.username, "display_name": user.display_name},
        ip_address=ip,
        user_agent=ua,
        db=db,
    )

    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
