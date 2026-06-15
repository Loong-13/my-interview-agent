"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nickname", sa.String(length=100), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_company", sa.String(length=200), nullable=True),
        sa.Column("target_role", sa.String(length=200), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=False),
        sa.Column("experience_level", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)

    op.create_table(
        "async_tasks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("celery_task_id", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_async_tasks_celery_task_id"), "async_tasks", ["celery_task_id"], unique=True)
    op.create_index(op.f("ix_async_tasks_project_id"), "async_tasks", ["project_id"], unique=False)
    op.create_index(op.f("ix_async_tasks_user_id"), "async_tasks", ["user_id"], unique=False)

    op.create_table(
        "interview_sessions",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(length=80), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_sessions_project_id"), "interview_sessions", ["project_id"], unique=False)

    op.create_table(
        "job_descriptions",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("position", sa.String(length=200), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_descriptions_project_id"), "job_descriptions", ["project_id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("evaluation_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_questions_project_id"), "questions", ["project_id"], unique=False)
    op.create_index(op.f("ix_questions_type"), "questions", ["type"], unique=False)

    op.create_table(
        "resumes",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("parsed_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("analysis_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resumes_project_id"), "resumes", ["project_id"], unique=False)

    op.create_table(
        "interview_messages",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_messages_session_id"), "interview_messages", ["session_id"], unique=False)

    op.create_table(
        "interview_reports",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommended_topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("improved_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_interview_reports_session_id"),
    )

    op.create_table(
        "match_reports",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resume_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_description_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("matched_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("missing_skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("interview_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("suggestions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_report", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_reports_project_id"), "match_reports", ["project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_match_reports_project_id"), table_name="match_reports")
    op.drop_table("match_reports")
    op.drop_table("interview_reports")
    op.drop_index(op.f("ix_interview_messages_session_id"), table_name="interview_messages")
    op.drop_table("interview_messages")
    op.drop_index(op.f("ix_resumes_project_id"), table_name="resumes")
    op.drop_table("resumes")
    op.drop_index(op.f("ix_questions_type"), table_name="questions")
    op.drop_index(op.f("ix_questions_project_id"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("ix_job_descriptions_project_id"), table_name="job_descriptions")
    op.drop_table("job_descriptions")
    op.drop_index(op.f("ix_interview_sessions_project_id"), table_name="interview_sessions")
    op.drop_table("interview_sessions")
    op.drop_index(op.f("ix_async_tasks_user_id"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_project_id"), table_name="async_tasks")
    op.drop_index(op.f("ix_async_tasks_celery_task_id"), table_name="async_tasks")
    op.drop_table("async_tasks")
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

