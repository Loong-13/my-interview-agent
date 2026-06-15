import uuid

from pydantic import BaseModel

from backend.app.schemas.common import ORMModel


class MatchReportCreate(BaseModel):
    resume_id: uuid.UUID
    job_description_id: uuid.UUID


class MatchReportResponse(ORMModel):
    id: uuid.UUID
    match_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    interview_focus: list[str]
    suggestions: list[str]

