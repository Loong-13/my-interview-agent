"""用户注册与登录流程。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppError
from backend.app.core.security import create_access_token, get_password_hash, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import RegisterRequest, TokenResponse


def register_user(db: Session, payload: RegisterRequest) -> User:
    # 创建用户前先拒绝重复邮箱。
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise AppError("EMAIL_ALREADY_REGISTERED", "Email already registered", status_code=409)

    user = User(
        email=str(payload.email),
        password_hash=get_password_hash(payload.password),
        nickname=payload.nickname,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    # 校验密码哈希，成功后签发访问令牌。
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Invalid email or password", status_code=401)

    return TokenResponse(access_token=create_access_token(str(user.id)))
