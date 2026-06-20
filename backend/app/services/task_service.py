"""Celery 异步任务的持久化辅助函数。"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.async_task import AsyncTask


def create_async_task(
    db: Session,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID | None,
    celery_task_id: str,
    task_type: str,
) -> AsyncTask:
    # 先写入本地任务记录，便于 API 立即返回可查询的任务句柄。
    task = AsyncTask(
        user_id=user_id,
        project_id=project_id,
        celery_task_id=celery_task_id,
        task_type=task_type,
        status="pending",
        progress=0,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_for_user(db: Session, task_id: uuid.UUID, user_id: uuid.UUID) -> AsyncTask:
    # 按当前用户限定任务查询，避免跨账号访问。
    task = db.scalar(select(AsyncTask).where(AsyncTask.id == task_id, AsyncTask.user_id == user_id))
    if task is None:
        raise AppError("TASK_NOT_FOUND", "Task not found", status_code=404)
    return task


def update_task_status(
    db: Session,
    *,
    celery_task_id: str,
    status: str,
    progress: int | None = None,
    result_json: dict[str, Any] | None = None,
    error_message: str | None = None,
) -> None:
    # Worker 在关键状态变化后调用，保证前端能看到进度。
    task = db.scalar(select(AsyncTask).where(AsyncTask.celery_task_id == celery_task_id))
    if task is None:
        return
    task.status = status
    if progress is not None:
        task.progress = progress
    if result_json is not None:
        task.result_json = result_json
    if error_message is not None:
        task.error_message = error_message
    db.commit()
