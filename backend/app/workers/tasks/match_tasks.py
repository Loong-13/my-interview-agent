"""简历-JD匹配报告生成任务。"""

import logging
import uuid

from app.agents.match_agent import MatchAgent
from app.core.database import SessionLocal
from app.models.job_description import JobDescription
from app.models.match_report import MatchReport
from app.models.resume import Resume
from app.services.task_service import update_task_status
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="match_report.generate")
def generate_match_report_task(
    self, project_id: str, resume_id: str, job_description_id: str
) -> dict[str, str]:
    """调用 MatchAgent 对比简历和 JD 分析，生成匹配报告。

    流程：
    1. 读取 resume.analysis_json 和 jd.analysis_json
    2. 调用 MatchAgent.analyze()
    3. 创建 MatchReport 记录
    """
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)

        resume = db.get(Resume, uuid.UUID(resume_id))
        if resume is None or not resume.analysis_json:
            raise ValueError("Resume not found or not analyzed yet")
        jd = db.get(JobDescription, uuid.UUID(job_description_id))
        if jd is None or not jd.analysis_json:
            raise ValueError("Job description not found or not analyzed yet")

        agent = MatchAgent(
            resume_analysis=resume.analysis_json,
            jd_analysis=jd.analysis_json,
        )
        analysis = agent.analyze()

        report = MatchReport(
            project_id=uuid.UUID(project_id),
            resume_id=uuid.UUID(resume_id),
            job_description_id=uuid.UUID(job_description_id),
            match_score=analysis.get("match_score", 0),
            matched_skills=analysis.get("matched_skills", []),
            missing_skills=analysis.get("missing_skills", []),
            interview_focus=analysis.get("interview_focus", []),
            suggestions=analysis.get("suggestions", []),
            raw_report=analysis,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={
                "match_report_id": str(report.id),
                "match_score": report.match_score,
            },
        )
        logger.info("Match report %s generated, score=%d", report.id, report.match_score)
        return {"match_report_id": str(report.id)}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db, celery_task_id=self.request.id, status="failed", progress=100, error_message=str(exc)
        )
        raise
    finally:
        db.close()
