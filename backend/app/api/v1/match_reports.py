"""匹配报告生成接口。"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppError
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.schemas.common import TaskAccepted
from app.schemas.match_report import MatchReportCreate
from app.services.project_service import get_project_for_user
from app.services.task_service import create_async_task
from app.workers.tasks.match_tasks import generate_match_report_task

router = APIRouter()


@router.post("/projects/{project_id}/match-reports", response_model=TaskAccepted)
def create_match_report(
    project_id: uuid.UUID,
    payload: MatchReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 开始评分前，简历和 JD 必须都属于同一个项目。
    project = get_project_for_user(db, project_id, current_user.id)
    resume = db.get(Resume, payload.resume_id)
    jd = db.get(JobDescription, payload.job_description_id)
    if resume is None or resume.project_id != project.id:
        raise AppError("RESUME_NOT_FOUND", "Resume not found", status_code=404)
    if jd is None or jd.project_id != project.id:
        raise AppError("JD_NOT_FOUND", "Job description not found", status_code=404)

    celery_result = generate_match_report_task.delay(str(project.id), str(resume.id), str(jd.id))
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="match_report.generate",
    )
    return TaskAccepted(task_id=task.id, status=task.status)
