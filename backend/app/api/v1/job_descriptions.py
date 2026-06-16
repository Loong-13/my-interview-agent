"""岗位描述相关接口。"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.job_description import JobDescription
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from backend.app.services.project_service import get_project_for_user
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.jd_tasks import analyze_jd_task

router = APIRouter()


@router.post("/projects/{project_id}/job-descriptions", response_model=JobDescriptionResponse)
def create_job_description(
    project_id: uuid.UUID,
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobDescription:
    # API 层只关注校验与持久化交接。
    get_project_for_user(db, project_id, current_user.id)
    jd = JobDescription(project_id=project_id, **payload.model_dump())
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


@router.post("/job-descriptions/{jd_id}/analyze", response_model=TaskAccepted)
def analyze_job_description(
    jd_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # JD 分析异步执行，客户端通过任务状态轮询结果。
    jd = db.get(JobDescription, jd_id)
    if jd is None:
        from app.core.exceptions import AppError

        raise AppError("JD_NOT_FOUND", "Job description not found", status_code=404)
    project = get_project_for_user(db, jd.project_id, current_user.id)
    celery_result = analyze_jd_task.delay(str(jd.id))
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="jd.analyze",
    )
    return TaskAccepted(task_id=task.id, status=task.status)
