import uuid

from pydantic import BaseModel, Field

from backend.app.schemas.common import Direction, ExperienceLevel, ORMModel, ProjectStatus


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    target_company: str | None = None
    target_role: str = Field(min_length=1, max_length=200)
    direction: Direction
    experience_level: ExperienceLevel = ExperienceLevel.intern


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_company: str | None = None
    target_role: str | None = Field(default=None, min_length=1, max_length=200)
    direction: Direction | None = None
    experience_level: ExperienceLevel | None = None
    status: ProjectStatus | None = None


class ProjectResponse(ORMModel):
    id: uuid.UUID
    name: str
    target_company: str | None
    target_role: str
    direction: str
    experience_level: str
    status: str
    latest_match_score: int | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int

