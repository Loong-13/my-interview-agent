import uuid
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.mixins import UUIDPrimaryKeyMixin


class MatchReport(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "match_reports"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id"), index=True, nullable=False
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("job_descriptions.id"), nullable=False
    )
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    interview_focus: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    suggestions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    raw_report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="match_reports")
    resume = relationship("Resume", back_populates="match_reports")
    job_description = relationship("JobDescription", back_populates="match_reports")

