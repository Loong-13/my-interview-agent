"""add knowledge base and question bank

Revision ID: 0002_add_knowledge_base
Revises: 0001_initial
Create Date: 2026-06-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0002_add_knowledge_base"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "knowledge_collections",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=50), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_collections_user_id"),
        "knowledge_collections",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("file_type", sa.String(length=50), nullable=True),
        sa.Column("content_type", sa.String(length=50), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["knowledge_collections.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_documents_collection_id"),
        "knowledge_documents",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_content_type"),
        "knowledge_documents",
        ["content_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_user_id"),
        "knowledge_documents",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["knowledge_collections.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_knowledge_chunks_collection_id"),
        "knowledge_chunks",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_document_id"),
        "knowledge_chunks",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_chunks_user_id"),
        "knowledge_chunks",
        ["user_id"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_embedding ON knowledge_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "question_bank_items",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_chunk_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("difficulty", sa.String(length=50), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("reference_answer", sa.Text(), nullable=True),
        sa.Column("evaluation_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["knowledge_collections.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"]),
        sa.ForeignKeyConstraint(["source_chunk_id"], ["knowledge_chunks.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_bank_items_collection_id"),
        "question_bank_items",
        ["collection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_bank_items_difficulty"),
        "question_bank_items",
        ["difficulty"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_bank_items_document_id"),
        "question_bank_items",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_question_bank_items_source_chunk_id"),
        "question_bank_items",
        ["source_chunk_id"],
        unique=False,
    )
    op.create_index(op.f("ix_question_bank_items_type"), "question_bank_items", ["type"], unique=False)
    op.create_index(
        op.f("ix_question_bank_items_user_id"),
        "question_bank_items",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "question_bank_item_embeddings",
        sa.Column("question_bank_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_bank_item_id"], ["question_bank_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_bank_item_embeddings_question_bank_item_id"),
        "question_bank_item_embeddings",
        ["question_bank_item_id"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX ix_question_bank_item_embeddings_vector ON question_bank_item_embeddings "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.add_column(
        "questions",
        sa.Column("question_bank_item_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column(
            "source_chunk_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_questions_question_bank_item_id"),
        "questions",
        ["question_bank_item_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_questions_question_bank_item_id_question_bank_items"),
        "questions",
        "question_bank_items",
        ["question_bank_item_id"],
        ["id"],
    )
    op.alter_column("questions", "source_chunk_ids", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_questions_question_bank_item_id_question_bank_items"),
        "questions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_questions_question_bank_item_id"), table_name="questions")
    op.drop_column("questions", "source_chunk_ids")
    op.drop_column("questions", "question_bank_item_id")

    op.execute("DROP INDEX IF EXISTS ix_question_bank_item_embeddings_vector")
    op.drop_index(
        op.f("ix_question_bank_item_embeddings_question_bank_item_id"),
        table_name="question_bank_item_embeddings",
    )
    op.drop_table("question_bank_item_embeddings")

    op.drop_index(op.f("ix_question_bank_items_user_id"), table_name="question_bank_items")
    op.drop_index(op.f("ix_question_bank_items_type"), table_name="question_bank_items")
    op.drop_index(op.f("ix_question_bank_items_source_chunk_id"), table_name="question_bank_items")
    op.drop_index(op.f("ix_question_bank_items_document_id"), table_name="question_bank_items")
    op.drop_index(op.f("ix_question_bank_items_difficulty"), table_name="question_bank_items")
    op.drop_index(op.f("ix_question_bank_items_collection_id"), table_name="question_bank_items")
    op.drop_table("question_bank_items")

    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding")
    op.drop_index(op.f("ix_knowledge_chunks_user_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_document_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_collection_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index(op.f("ix_knowledge_documents_user_id"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_content_type"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_collection_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    op.drop_index(op.f("ix_knowledge_collections_user_id"), table_name="knowledge_collections")
    op.drop_table("knowledge_collections")
