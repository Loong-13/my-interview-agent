"""匹配报告业务逻辑层。"""

import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.services.task_service import create_async_task
from app.workers.tasks.match_tasks import generate_match_report_task


def dispatch_match_task(
    db: Session,
    project_id: uuid.UUID,
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
    user: User,
) -> tuple[uuid.UUID, str]:
    """提交匹配报告生成任务到 Celery。

    Returns:
        (task_id, task_status)
    """
    celery_result = generate_match_report_task.delay(
        str(project_id), str(resume_id), str(jd_id)
    )
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="match_report.generate",
    )
    return task.id, task.status
