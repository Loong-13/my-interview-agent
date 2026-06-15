import uuid

from pydantic import BaseModel

from backend.app.schemas.common import Direction, ORMModel


class ResumeUploadResponse(ORMModel):
    resume_id: uuid.UUID
    file_name: str
    status: str


class ResumeParseResponse(ORMModel):
    resume_id: uuid.UUID
    status: str
    raw_text: str | None = None


class ResumeAnalyzeRequest(BaseModel):
    target_direction: Direction | None = None


class ResumeAnalyzeResponse(BaseModel):
    detected_direction: str
    skills: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    project_deep_dive_points: list[str] = []

