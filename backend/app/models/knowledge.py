import uuid
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.core.database import Base
from backend.app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeCollection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_collections"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)

    user = relationship("User", back_populates="knowledge_collections")
    documents = relationship("KnowledgeDocument", back_populates="collection")
    chunks = relationship("KnowledgeChunk", back_populates="collection")
    question_bank_items = relationship("QuestionBankItem", back_populates="collection")


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_collections.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_url: Mapped[str | None] = mapped_column(String(500))
    file_type: Mapped[str | None] = mapped_column(String(50))
    content_type: Mapped[str] = mapped_column(
        String(50), default="interview_notes", index=True, nullable=False
    )
    raw_text: Mapped[str | None] = mapped_column(Text)
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, default=dict, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    parse_error: Mapped[str | None] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="knowledge_documents")
    collection = relationship("KnowledgeCollection", back_populates="documents")
    chunks = relationship("KnowledgeChunk", back_populates="document")
    question_bank_items = relationship("QuestionBankItem", back_populates="document")


class KnowledgeChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_chunks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_collections.id"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), index=True, nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    embedding_model: Mapped[str | None] = mapped_column(String(100))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User", back_populates="knowledge_chunks")
    collection = relationship("KnowledgeCollection", back_populates="chunks")
    document = relationship("KnowledgeDocument", back_populates="chunks")
    question_bank_items = relationship("QuestionBankItem", back_populates="source_chunk")


class QuestionBankItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "question_bank_items"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True, nullable=False
    )
    collection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_collections.id"), index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_documents.id"), index=True
    )
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_chunks.id"), index=True
    )
    type: Mapped[str] = mapped_column(String(80), index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intern", index=True, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str | None] = mapped_column(Text)
    evaluation_points: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    quality_score: Mapped[int | None] = mapped_column(Integer)

    user = relationship("User", back_populates="question_bank_items")
    collection = relationship("KnowledgeCollection", back_populates="question_bank_items")
    document = relationship("KnowledgeDocument", back_populates="question_bank_items")
    source_chunk = relationship("KnowledgeChunk", back_populates="question_bank_items")
    embeddings = relationship("QuestionBankItemEmbedding", back_populates="question_bank_item")


class QuestionBankItemEmbedding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "question_bank_item_embeddings"

    question_bank_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_bank_items.id"), index=True, nullable=False
    )
    embedding_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    question_bank_item = relationship("QuestionBankItem", back_populates="embeddings")
