import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.project import Project
from backend.app.models.user import User
from backend.app.schemas.project import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from backend.app.services.project_service import (
    archive_project,
    create_project,
    get_project_for_user,
    list_projects,
    update_project,
)

router = APIRouter()


@router.post("", response_model=ProjectResponse)
def create(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return create_project(db, current_user.id, payload)


@router.get("", response_model=ProjectListResponse)
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    items = list_projects(db, current_user.id)
    return ProjectListResponse(items=items, total=len(items))


@router.get("/{project_id}", response_model=ProjectResponse)
def get_one(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return get_project_for_user(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    return update_project(db, project_id, current_user.id, payload)


@router.delete("/{project_id}", status_code=204)
def delete(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    archive_project(db, project_id, current_user.id)
    return Response(status_code=204)

