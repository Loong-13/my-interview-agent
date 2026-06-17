"""面试会话业务逻辑层。"""

import uuid

from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.interview_tasks import generate_interview_report_task


def dispatch_report_task(
    db: Session,
    session_id: uuid.UUID,
    user: User,
    project_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    """提交面试报告生成任务到 Celery。

    Returns:
        (task_id, task_status)
    """
    celery_result = generate_interview_report_task.delay(str(session_id))
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="interview_report.generate",
    )
    return task.id, task.status
