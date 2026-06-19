"""个人知识库相关请求和响应模型。"""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from backend.app.schemas.common import ORMModel


class KnowledgeVisibility(StrEnum):
    private = "private"
    shared = "shared"
    public = "public"


class KnowledgeContentType(StrEnum):
    interview_notes = "interview_notes"
    question_bank = "question_bank"
    experience_post = "experience_post"
    project_doc = "project_doc"
    course_note = "course_note"
    other = "other"


class KnowledgeCollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    visibility: KnowledgeVisibility = KnowledgeVisibility.private


class KnowledgeCollectionResponse(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None
    visibility: str
    created_at: datetime
    updated_at: datetime


class KnowledgeCollectionListResponse(BaseModel):
    items: list[KnowledgeCollectionResponse]
    total: int


class KnowledgeTextDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_type: KnowledgeContentType = KnowledgeContentType.interview_notes
    raw_text: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeDocumentResponse(ORMModel):
    id: uuid.UUID
    collection_id: uuid.UUID | None
    title: str
    file_name: str | None
    file_type: str | None
    content_type: str
    status: str
    parse_error: str | None
    chunk_count: int
    indexed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentListResponse(BaseModel):
    items: list[KnowledgeDocumentResponse]
    total: int


class KnowledgeDocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    status: str


class KnowledgeDocumentIndexRequest(BaseModel):
    extract_questions: bool = False


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    collection_ids: list[uuid.UUID] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchItem(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    title: str | None
    content: str
    score: float
    metadata: dict[str, Any]


class KnowledgeSearchResponse(BaseModel):
    items: list[KnowledgeSearchItem]

