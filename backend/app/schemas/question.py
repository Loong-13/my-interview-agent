import uuid

from pydantic import BaseModel, Field

from app.schemas.common import InterviewMode, ORMModel


class QuestionGenerateRequest(BaseModel):
    mode: InterviewMode
    difficulty: str = "intern"
    count: int = Field(default=10, ge=1, le=20)
    focus: list[str] = Field(default_factory=list)


class QuestionGenerateFromKnowledgeRequest(QuestionGenerateRequest):
    collection_ids: list[uuid.UUID] = Field(default_factory=list)


class QuestionResponse(ORMModel):
    id: uuid.UUID
    type: str
    difficulty: str
    question: str
    evaluation_points: list[str]
    reference_answer: str = ""
    source_chunk_ids: list[str] = Field(default_factory=list)
    source: str


class QuestionListResponse(BaseModel):
    questions: list[QuestionResponse]
