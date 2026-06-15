import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Direction(StrEnum):
    python_backend = "python_backend"
    agent_engineer = "agent_engineer"
    llm_application = "llm_application"


class ExperienceLevel(StrEnum):
    intern = "intern"
    new_grad = "new_grad"


class ProjectStatus(StrEnum):
    active = "active"
    archived = "archived"


class TaskStatus(StrEnum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class InterviewMode(StrEnum):
    python_basic = "python_basic"
    python_backend_project = "python_backend_project"
    fastapi_backend = "fastapi_backend"
    agent_basic = "agent_basic"
    rag_project_deep_dive = "rag_project_deep_dive"


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TaskAccepted(ORMModel):
    task_id: uuid.UUID
    status: TaskStatus


class TimestampedModel(ORMModel):
    created_at: datetime
    updated_at: datetime

