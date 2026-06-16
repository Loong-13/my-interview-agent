"""SQLAlchemy 引擎、会话工厂和声明式基类定义。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


class Base(DeclarativeBase):
    # 所有 ORM 模型都继承这个基类。
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    # FastAPI 依赖：每个请求打开一个数据库会话，并在结束后关闭。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
