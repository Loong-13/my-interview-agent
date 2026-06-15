import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppError
from backend.app.models.match_report import MatchReport
from backend.app.models.project import Project
from backend.app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate


def create_project(db: Session, user_id: uuid.UUID, payload: ProjectCreate) -> Project:
    project = Project(user_id=user_id, **payload.model_dump(mode="json"))
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: uuid.UUID) -> list[ProjectResponse]:
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
    updates = payload.model_dump(exclude_unset=True, mode="json")
    for key, value in updates.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def archive_project(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
    project = get_project_for_user(db, project_id, user_id)
    project.status = "archived"
    db.commit()

