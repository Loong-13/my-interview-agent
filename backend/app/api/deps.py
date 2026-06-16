"""认证与请求级资源相关的 FastAPI 依赖。"""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.exceptions import AppError
from backend.app.core.security import decode_access_token
from backend.app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # 要求请求携带 Authorization 头，并把令牌解析成真实用户记录。
    if credentials is None:
        raise AppError("UNAUTHORIZED", "Authentication required", status_code=401)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (PyJWTError, ValueError, TypeError):
        raise AppError("UNAUTHORIZED", "Invalid token", status_code=401) from None

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise AppError("UNAUTHORIZED", "User not found", status_code=401)
    return user
