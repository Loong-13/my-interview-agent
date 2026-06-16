"""简历上传、解析和分析接口。"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppError
from backend.app.models.resume import Resume
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.resume import ResumeAnalyzeRequest, ResumeParseResponse, ResumeUploadResponse
from backend.app.services.project_service import get_project_for_user
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.resume_tasks import analyze_resume_task, parse_resume_task

router = APIRouter()


@router.post("/projects/{project_id}/resumes", response_model=ResumeUploadResponse)
def upload_resume(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeUploadResponse:
    # 只允许支持的文档格式进入处理流程。
    get_project_for_user(db, project_id, current_user.id)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise AppError("UNSUPPORTED_FILE_TYPE", "Only PDF, DOCX, and TXT resumes are supported")

    upload_dir = Path(settings.upload_dir) / "resumes" / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}{suffix}"
    content = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise AppError("FILE_TOO_LARGE", "Uploaded file is too large")
    file_path.write_bytes(content)

    resume = Resume(
        project_id=project_id,
        file_name=file.filename,
        file_url=str(file_path),
        file_type=suffix.removeprefix("."),
        status="uploaded",
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return ResumeUploadResponse(resume_id=resume.id, file_name=resume.file_name or "", status=resume.status)


@router.post("/resumes/{resume_id}/parse", response_model=TaskAccepted)
def parse_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 解析可能涉及文件 I/O 或类似 OCR 的耗时操作，因此交给 Celery 处理。
    resume = db.scalar(select(Resume).where(Resume.id == resume_id))
    if resume is None:
        raise AppError("RESUME_NOT_FOUND", "Resume not found", status_code=404)
    project = get_project_for_user(db, resume.project_id, current_user.id)
    celery_result = parse_resume_task.delay(str(resume.id))
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="resume.parse",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.post("/resumes/{resume_id}/analyze", response_model=TaskAccepted)
def analyze_resume(
    resume_id: uuid.UUID,
    payload: ResumeAnalyzeRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 分析时可传入方向提示，用于后续定制 Agent 提示词。
    resume = db.scalar(select(Resume).where(Resume.id == resume_id))
    if resume is None:
        raise AppError("RESUME_NOT_FOUND", "Resume not found", status_code=404)
    project = get_project_for_user(db, resume.project_id, current_user.id)
    target_direction = payload.target_direction.value if payload and payload.target_direction else None
    celery_result = analyze_resume_task.delay(str(resume.id), target_direction)
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=project.id,
        celery_task_id=celery_result.id,
        task_type="resume.analyze",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("/resumes/{resume_id}", response_model=ResumeParseResponse)
def get_resume(
    resume_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResumeParseResponse:
    # 返回解析文本前复用项目归属校验。
    resume = db.scalar(select(Resume).where(Resume.id == resume_id))
    if resume is None:
        raise AppError("RESUME_NOT_FOUND", "Resume not found", status_code=404)
    get_project_for_user(db, resume.project_id, current_user.id)
    return ResumeParseResponse(resume_id=resume.id, status=resume.status, raw_text=resume.raw_text)
