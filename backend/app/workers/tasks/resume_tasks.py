"""简历解析与分析的后台任务。"""

import uuid

from backend.app.core.database import SessionLocal
from backend.app.models.resume import Resume
from backend.app.services.task_service import update_task_status
from backend.app.utils.document_parser import parse_document_text
from backend.app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="resume.parse")
def parse_resume_task(self, resume_id: str) -> dict[str, str]:
    # Celery Worker 不在 FastAPI 请求上下文中运行，因此需要单独创建会话。
    db = SessionLocal()
    try:
        # 在执行耗时文件解析前，先把任务标记为运行中。
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        resume = db.get(Resume, uuid.UUID(resume_id))
        if resume is None:
            raise ValueError("Resume not found")
        if not resume.file_url:
            raise ValueError("Resume file path is empty")

        raw_text = parse_document_text(resume.file_url, resume.file_type)
        resume.raw_text = raw_text
        resume.status = "parsed"
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"resume_id": str(resume.id)},
        )
        return {"resume_id": str(resume.id), "status": "parsed"}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="failed",
            progress=100,
            error_message=str(exc),
        )
        raise
    finally:
        db.close()


@celery_app.task(bind=True, name="resume.analyze")
def analyze_resume_task(self, resume_id: str, target_direction: str | None = None) -> dict[str, str]:
    # 这里仍是占位实现；输出结构会与未来 Agent 的返回契约保持一致。
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        resume = db.get(Resume, uuid.UUID(resume_id))
        if resume is None:
            raise ValueError("Resume not found")

        # 在真正接入 ResumeAgent 前先使用占位分析结果。
        resume.analysis_json = {
            "prompt_version": "resume_analysis_stub_v1",
            "detected_direction": target_direction or "unknown",
            "skills": [],
            "weaknesses": ["ResumeAgent is not implemented yet"],
            "suggestions": ["Wire ResumeAgent to generate structured analysis"],
            "project_deep_dive_points": [],
        }
        resume.status = "analyzed"
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"resume_id": str(resume.id)},
        )
        return {"resume_id": str(resume.id), "status": "analyzed"}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="failed",
            progress=100,
            error_message=str(exc),
        )
        raise
    finally:
        db.close()
