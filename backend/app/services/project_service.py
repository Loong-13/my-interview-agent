"""用户项目的增删改查辅助函数。"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.match_report import MatchReport
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


def create_project(db: Session, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
    # 请求数据已由 Pydantic 校验，这里只负责持久化 ORM 对象。
    project = Project(user_id=user_id, **payload.model_dump(mode="json"))
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: uuid.UUID) -> list[ProjectResponse]:
    # 附带最近一次匹配分数，便于列表页直接展示。
    projects = db.scalars(
        select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
    ).all()

    responses: list[ProjectResponse] = []
    for project in projects:
        latest_score = db.scalar(
            select(MatchReport.match_score)
            .where(MatchReport.project_id == project.id)
            .order_by(MatchReport.created_at.desc())
            .limit(1)
        )
        item = ProjectResponse.model_validate(project)
        item.latest_match_score = latest_score
        responses.append(item)
    return responses


def get_project_for_user(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user_id))
    if project is None:
        raise AppError("PROJECT_NOT_FOUND", "Project not found", status_code=404)
    return project


def update_project(
    db: Session, project_id: uuid.UUID, user_id: uuid.UUID, payload: ProjectUpdate
) -> Project:
    project = get_project_for_user(db, project_id, user_id)
    # 只用客户端显式传入的字段覆盖已有值。
    updates = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in updates.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def archive_project(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    # 项目采用软归档，历史简历和报告仍能保持关联。
    project = get_project_for_user(db, project_id, user_id)
    project.status = "archived"
    db.commit()
