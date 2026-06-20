"""简历解析与分析的后台任务。"""

import logging
import uuid

from app.agents.resume_agent import ResumeAgent
from app.core.database import SessionLocal
from app.models.resume import Resume
from app.services.task_service import update_task_status
from app.utils.document_parser import parse_document_text
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="resume.parse")
def parse_resume_task(self, resume_id: str) -> dict[str, str]:
    # Celery Worker 不在 FastAPI 请求上下文中运行，因此需要单独创建会话。
    db = SessionLocal()
    try:
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
    """调用 ResumeAgent 对已解析的简历进行 AI 分析。

    流程：
    1. 从 DB 读取简历 raw_text
    2. 调用 ResumeAgent.analyze() 获取结构化分析
    3. JSON 解析与 Pydantic 校验（Agent 内部重试）
    4. 写入 resumes.analysis_json 并更新状态为 analyzed
    """
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        resume = db.get(Resume, uuid.UUID(resume_id))
        if resume is None:
            raise ValueError(f"Resume {resume_id} not found")
        if not resume.raw_text:
            raise ValueError("Resume raw_text is empty, run parse first")

        direction = target_direction or resume.project.direction or "agent_engineer"

        # 调用 ResumeAgent 分析简历
        agent = ResumeAgent(resume_text=resume.raw_text, target_direction=direction)
        analysis = agent.analyze()

        # 写入分析结果
        resume.analysis_json = analysis
        resume.status = "analyzed"
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={
                "resume_id": str(resume.id),
                "detected_direction": analysis.get("detected_direction"),
                "skill_count": len(analysis.get("skills", [])),
            },
        )
        logger.info("Resume %s analyzed as %s", resume_id, analysis.get("detected_direction"))
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
        logger.error("Resume analysis failed for %s: %s", resume_id, exc)
        raise
    finally:
        db.close()
