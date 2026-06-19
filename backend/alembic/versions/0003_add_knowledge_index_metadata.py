"""add knowledge index metadata

Revision ID: 0003_add_knowledge_index_metadata
Revises: 0002_add_knowledge_base
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_knowledge_index_metadata"
down_revision: str | None = "0002_add_knowledge_base"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("knowledge_documents", sa.Column("parse_error", sa.Text(), nullable=True))
    op.add_column(
        "knowledge_documents",
        sa.Column("chunk_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "knowledge_chunks",
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
    )
    op.add_column("knowledge_chunks", sa.Column("content_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_chunks", "content_hash")
    op.drop_column("knowledge_chunks", "embedding_model")

    op.drop_column("knowledge_documents", "indexed_at")
    op.drop_column("knowledge_documents", "chunk_count")
    op.drop_column("knowledge_documents", "parse_error")
