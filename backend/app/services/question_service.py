"""面试题生成业务逻辑层。"""

import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.task_service import create_async_task
from app.workers.tasks.question_tasks import generate_questions_task


def dispatch_question_task(
    db: Session,
    project_id: uuid.UUID,
    user: User,
    mode: str,
    difficulty: str,
    count: int,
    focus: list[str] | None = None,
) -> tuple[uuid.UUID, str]:
    """提交面试题生成任务到 Celery。

    Returns:
        (task_id, task_status)
    """
    celery_result = generate_questions_task.delay(
        str(project_id), mode, difficulty, count, focus or []
    )
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="questions.generate",
    )
    return task.id, task.status
