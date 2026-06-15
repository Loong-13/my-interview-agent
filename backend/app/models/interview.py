import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class InterviewSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interview_sessions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(80), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intern", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project = relationship("Project", back_populates="interview_sessions")
    messages = relationship("InterviewMessage", back_populates="session")
    report = relationship("InterviewReport", back_populates="session", uselist=False)


class InterviewMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    question_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    feedback_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("InterviewSession", back_populates="messages")


class InterviewReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "interview_reports"
    __table_args__ = (UniqueConstraint("session_id", name="uq_interview_reports_session_id"),)

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interview_sessions.id"), nullable=False
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    scores: Mapped[dict[str, int]] = mapped_column(JSONB, default=dict, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    suggestions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    recommended_topics: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    improved_answers: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)
    raw_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("InterviewSession", back_populates="report")

