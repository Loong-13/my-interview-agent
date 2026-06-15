import uuid

from pydantic import BaseModel, Field

from backend.app.schemas.common import ORMModel


class JobDescriptionCreate(BaseModel):
    company: str | None = None
    position: str | None = None
    raw_text: str = Field(min_length=1)


class JobDescriptionResponse(ORMModel):
    id: uuid.UUID
    company: str | None
    position: str | None
    raw_text: str


class JDAnalyzeResponse(BaseModel):
    direction: str
    required_skills: list[str]
    bonus_skills: list[str]
    interview_topics: list[str]

