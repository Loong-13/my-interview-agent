import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.task import AsyncTaskResponse
from app.services.task_service import get_task_for_user

router = APIRouter()


@router.get("/{task_id}", response_model=AsyncTaskResponse)
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AsyncTaskResponse:
    task = get_task_for_user(db, task_id, current_user.id)
    return AsyncTaskResponse(
        id=task.id,
        task_type=task.task_type,
        status=task.status,
        progress=task.progress,
        result=task.result_json,
        error_message=task.error_message,
    )

