"""项目请求与响应 Schema。"""

import uuid

from pydantic import BaseModel, Field

from app.schemas.common import Direction, ExperienceLevel, ORMModel, ProjectStatus


class ProjectCreate(BaseModel):
    # 创建项目只要求前端初始可编辑的字段。
    name: str = Field(min_length=1, max_length=200)
    target_company: str | None = None
    target_role: str = Field(min_length=1, max_length=200)
    direction: Direction
    experience_level: ExperienceLevel = ExperienceLevel.intern


class ProjectUpdate(BaseModel):
    # 所有字段都是可选的，让 PATCH 保持局部更新和幂等。
    name: str | None = Field(default=None, min_length=1, max_length=200)
    target_company: str | None = None
    target_role: str | None = Field(default=None, min_length=1, max_length=200)
    direction: Direction | None = None
    experience_level: ExperienceLevel | None = None
    status: ProjectStatus | None = None


class ProjectResponse(ORMModel):
    # 响应模型对应数据库记录，并额外包含计算得到的分数。
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
