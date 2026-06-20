"""个人题库相关请求和响应模型。"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class QuestionBankSource(StrEnum):
    manual = "manual"
    document_extract = "document_extract"
    ai_generated = "ai_generated"
    imported = "imported"


class QuestionBankItemCreate(BaseModel):
    collection_id: uuid.UUID | None = None
    type: str = Field(min_length=1, max_length=80)
    difficulty: str = "intern"
    question: str = Field(min_length=1)
    reference_answer: str | None = None
    evaluation_points: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class QuestionBankItemResponse(ORMModel):
    id: uuid.UUID
    collection_id: uuid.UUID | None
    document_id: uuid.UUID | None
    source_chunk_id: uuid.UUID | None
    type: str
    difficulty: str
    question: str
    reference_answer: str | None
    evaluation_points: list[str]
    tags: list[str]
    source: str
    quality_score: int | None
    created_at: datetime
    updated_at: datetime


class QuestionBankItemListResponse(BaseModel):
    items: list[QuestionBankItemResponse]
    total: int


class QuestionBankImportRequest(BaseModel):
    collection_id: uuid.UUID
    format: str = "qa_markdown"
    content: str = Field(min_length=1)

