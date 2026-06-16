from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))

    projects = relationship("Project", back_populates="user")
    async_tasks = relationship("AsyncTask", back_populates="user")
    knowledge_collections = relationship("KnowledgeCollection", back_populates="user")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="user")
    knowledge_chunks = relationship("KnowledgeChunk", back_populates="user")
    question_bank_items = relationship("QuestionBankItem", back_populates="user")
