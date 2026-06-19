"""个人题库接口。"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.question_bank import (
    QuestionBankImportRequest,
    QuestionBankItemCreate,
    QuestionBankItemListResponse,
    QuestionBankItemResponse,
)
from backend.app.services.question_bank_service import create_question_bank_item, list_question_bank_items
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.knowledge_tasks import import_question_bank_task

router = APIRouter()


@router.post("/items", response_model=QuestionBankItemResponse)
def create_item(
    payload: QuestionBankItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionBankItemResponse:
    # 手动新增是 MVP 中最可靠的高质量题库入口。
    item = create_question_bank_item(db, user_id=current_user.id, payload=payload)
    return QuestionBankItemResponse.model_validate(item)


@router.get("/items", response_model=QuestionBankItemListResponse)
def get_items(
    collection_id: uuid.UUID | None = None,
    type: str | None = Query(default=None),
    difficulty: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuestionBankItemListResponse:
    # 查询支持常见筛选项，复杂全文检索后续再演进。
    items = list_question_bank_items(
        db,
        user_id=current_user.id,
        collection_id=collection_id,
        type_=type,
        difficulty=difficulty,
        tag=tag,
        keyword=keyword,
    )
    return QuestionBankItemListResponse(
        items=[QuestionBankItemResponse.model_validate(item) for item in items],
        total=len(items),
    )


@router.post("/import", response_model=TaskAccepted)
def import_items(
    payload: QuestionBankImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 批量导入可能解析出很多题目，走异步任务保持接口响应稳定。
    celery_result = import_question_bank_task.delay(
        str(current_user.id),
        str(payload.collection_id),
        payload.format,
        payload.content,
    )
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=None,
        celery_task_id=celery_result.id,
        task_type="question_bank.import",
    )
    return TaskAccepted(task_id=task.id, status=task.status)
