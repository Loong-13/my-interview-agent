"""项目实体，用于连接用户与其面试准备工作区。"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    # 项目承载候选人的简历、JD、报告、题目和面试等准备材料。
    __tablename__ = "projects"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_company: Mapped[str | None] = mapped_column(String(200))
    target_role: Mapped[str] = mapped_column(String(200), nullable=False)
    direction: Mapped[str] = mapped_column(String(50), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(50), default="intern", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # 关系字段用于 ORM 导航和关联读取。
    user = relationship("User", back_populates="projects")
    resumes = relationship("Resume", back_populates="project")
    job_descriptions = relationship("JobDescription", back_populates="project")
    match_reports = relationship("MatchReport", back_populates="project")
    questions = relationship("Question", back_populates="project")
    interview_sessions = relationship("InterviewSession", back_populates="project")
    async_tasks = relationship("AsyncTask", back_populates="project")
