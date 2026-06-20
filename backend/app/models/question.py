import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class Question(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "questions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True, nullable=False
    )
    question_bank_item_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_bank_items.id"), index=True
    )
    type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intern", nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str | None] = mapped_column(Text)
    evaluation_points: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    source_chunk_ids: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="ai_generated", nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="questions")
    question_bank_item = relationship("QuestionBankItem")
