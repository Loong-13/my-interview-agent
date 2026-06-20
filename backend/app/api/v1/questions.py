"""面试题生成与列表接口。"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.question import Question
from app.models.user import User
from app.schemas.common import TaskAccepted
from app.schemas.question import (
    QuestionGenerateFromKnowledgeRequest,
    QuestionGenerateRequest,
    QuestionListResponse,
    QuestionResponse,
)
from app.services.knowledge_base_service import ensure_collections_belong_to_user
from app.services.project_service import get_project_for_user
from app.services.task_service import create_async_task
from app.workers.tasks.question_tasks import generate_questions_from_knowledge_task, generate_questions_task

router = APIRouter()


@router.post("/projects/{project_id}/questions/generate", response_model=TaskAccepted)
def generate_questions(
    project_id: uuid.UUID,
    payload: QuestionGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 题目生成在 Worker 中执行，客户端这里只拿到任务句柄。
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


@router.post("/projects/{project_id}/questions/generate-from-knowledge", response_model=TaskAccepted)
def generate_questions_from_knowledge(
    project_id: uuid.UUID,
    payload: QuestionGenerateFromKnowledgeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 知识库增强出题先校验集合归属，再异步检索和生成。
    project = get_project_for_user(db, project_id, current_user.id)
    ensure_collections_belong_to_user(db, collection_ids=payload.collection_ids, user_id=current_user.id)
    celery_result = generate_questions_from_knowledge_task.delay(
        str(project.id),
        str(current_user.id),
        payload.mode.value,
        payload.difficulty,
        payload.count,
        [str(collection_id) for collection_id in payload.collection_ids],
        payload.focus,
    )
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="questions.generate_from_knowledge",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("/projects/{project_id}/questions", response_model=QuestionListResponse)
def list_questions(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionListResponse:
    # 最新题目排在前面，符合常见复盘浏览顺序。
    project = get_project_for_user(db, project_id, current_user.id)
    questions = db.scalars(
        select(Question).where(Question.project_id == project.id).order_by(Question.created_at.desc())
    ).all()
    return QuestionListResponse(
        questions=[QuestionResponse.model_validate(question) for question in questions]
    )
