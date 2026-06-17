"""简历业务逻辑层。

负责协调简历上传后的解析和分析步骤，
把 Controller（API）和 Worker（Celery）之间的调度逻辑收拢到这里。
"""

import uuid

from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppError
from backend.app.models.resume import Resume
from backend.app.models.user import User
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.resume_tasks import analyze_resume_task, parse_resume_task


def dispatch_parse_task(
    db: Session,
    resume_id: uuid.UUID,
    user: User,
    project_id: uuid.UUID,
) -> tuple[uuid.UUID, str]:
    """提交简历解析任务到 Celery。

    Returns:
        (task_id, task_status)
    """
    celery_result = parse_resume_task.delay(str(resume_id))
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="resume.parse",
    )
    return task.id, task.status


def dispatch_analyze_task(
    db: Session,
    resume_id: uuid.UUID,
    user: User,
    project_id: uuid.UUID,
    target_direction: str | None = None,
) -> tuple[uuid.UUID, str]:
    """提交简历 AI 分析任务到 Celery。

    Args:
        target_direction: 目标岗位方向，为空时降级使用项目的 direction。

    Returns:
        (task_id, task_status)
    """
    celery_result = analyze_resume_task.delay(str(resume_id), target_direction)
    task = create_async_task(
        db,
        user_id=user.id,
        project_id=project_id,
        celery_task_id=celery_result.id,
        task_type="resume.analyze",
    )
    return task.id, task.status


def get_resume_analysis(db: Session, resume_id: uuid.UUID) -> dict | None:
    """获取简历的最新 AI 分析结果。"""
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise AppError("RESUME_NOT_FOUND", "Resume not found", status_code=404)
    return resume.analysis_json
