import uuid
from typing import Any

from pydantic import BaseModel

from app.schemas.common import InterviewMode, ORMModel


class InterviewCreate(BaseModel):
    mode: InterviewMode
    difficulty: str = "intern"


class InterviewCreateResponse(BaseModel):
    session_id: uuid.UUID
    status: str


class InterviewStartResponse(BaseModel):
    session_id: uuid.UUID
    first_question: str


class InterviewAnswerRequest(BaseModel):
    answer: str


class InterviewAnswerResponse(BaseModel):
    feedback: str
    next_question: str
    should_continue: bool


class InterviewMessageResponse(ORMModel):
    id: uuid.UUID
    role: str
    content: str
    feedback_json: dict[str, Any] | None = None


class InterviewReportResponse(ORMModel):
    id: uuid.UUID
    overall_score: int
    scores: dict[str, int]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    recommended_topics: list[str]

