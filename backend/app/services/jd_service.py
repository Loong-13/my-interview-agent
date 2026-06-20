"""岗位描述业务逻辑层。

负责协调 JD 保存后的分析步骤，
把 Controller（API）和 Worker（Celery）之间的调度逻辑收拢到这里。
"""

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.job_description import JobDescription
from app.models.user import User
from app.services.task_service import create_async_task
from app.workers.tasks.jd_tasks import analyze_jd_task


def dispatch_analyze_task(
    db: Session,
    jd_id: uuid.UUID,
    user: User,
    project_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    """提交 JD AI 分析任务到 Celery。

    Returns:
        (task_id, task_status)
    """
    celery_result = analyze_jd_task.delay(str(jd_id))
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="jd.analyze",
    )
    return task.id, task.status


def get_jd_analysis(db: Session, jd_id: uuid.UUID) -> dict | None:
    """获取 JD 的最新 AI 分析结果。"""
    jd = db.get(JobDescription, jd_id)
    if jd is None:
        raise AppError("JD_NOT_FOUND", "Job description not found", status_code=404)
    return jd.analysis_json
