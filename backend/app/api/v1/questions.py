import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.question import Question
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.question import QuestionGenerateRequest, QuestionListResponse, QuestionResponse
from backend.app.services.project_service import get_project_for_user
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.question_tasks import generate_questions_task

router = APIRouter()


@router.post("/projects/{project_id}/questions/generate", response_model=TaskAccepted)
def generate_questions(
    project_id: uuid.UUID,
    payload: QuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    project = get_project_for_user(db, project_id, current_user.id)
    celery_result = generate_questions_task.delay(
        str(project.id),
        payload.mode.value,
        payload.difficulty,
        payload.count,
        payload.focus,
    )
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="questions.generate",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("/projects/{project_id}/questions", response_model=QuestionListResponse)
def list_questions(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionListResponse:
    project = get_project_for_user(db, project_id, current_user.id)
    questions = db.scalars(
        select(Question).where(Question.project_id == project.id).order_by(Question.created_at.desc())
    ).all()
    return QuestionListResponse(
        questions=[QuestionResponse.model_validate(question) for question in questions]
    )

