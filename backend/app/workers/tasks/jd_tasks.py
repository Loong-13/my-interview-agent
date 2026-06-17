"""岗位描述解析与分析的后台任务。"""

import logging
import uuid

from backend.app.agents.jd_analyzer_agent import JDAnalyzerAgent
from backend.app.core.database import SessionLocal
from backend.app.models.job_description import JobDescription
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="jd.analyze")
def analyze_jd_task(self, job_description_id: str) -> dict[str, str]:
    """调用 JDAnalyzerAgent 对 JD 进行 AI 分析。

    流程：
    1. 从 DB 读取 JD raw_text
    2. 调用 JDAnalyzerAgent.analyze() 获取结构化分析
    3. JSON 解析与校验（Agent 内部重试）
    4. 写入 job_descriptions.analysis_json
    """
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        jd = db.get(JobDescription, uuid.UUID(job_description_id))
        if jd is None:
            raise ValueError(f"Job description {job_description_id} not found")
        if not jd.raw_text:
            raise ValueError("Job description raw_text is empty, save the JD first")

        # 调用 JDAnalyzerAgent 分析 JD
        agent = JDAnalyzerAgent(jd_text=jd.raw_text)
        analysis = agent.analyze()

        # 写入分析结果
        jd.analysis_json = analysis
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={
                "job_description_id": str(jd.id),
                "direction": analysis.get("direction"),
                "required_skill_count": len(analysis.get("required_skills", [])),
            },
        )
        logger.info("JD %s analyzed as %s", job_description_id, analysis.get("direction"))
        return {"job_description_id": str(jd.id), "status": "analyzed"}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="failed",
            progress=100,
            error_message=str(exc),
        )
        logger.error("JD analysis failed for %s: %s", job_description_id, exc)
        raise
    finally:
        db.close()
