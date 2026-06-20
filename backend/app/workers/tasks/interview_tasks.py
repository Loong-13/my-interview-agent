"""面试报告生成任务。"""

import logging
import uuid

from sqlalchemy import select

from app.agents.evaluator_agent import EvaluatorAgent
from app.core.database import SessionLocal
from app.models.interview import InterviewMessage, InterviewReport, InterviewSession
from app.services.task_service import update_task_status
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="interview_report.generate")
def generate_interview_report_task(self, session_id: str) -> dict[str, str]:
    """调用 EvaluatorAgent 对完整面试记录做多维度评分。

    流程：
    1. 读取面试消息记录
    2. 调用 EvaluatorAgent.analyze()
    3. 创建 InterviewReport 记录
    """
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        session = db.get(InterviewSession, uuid.UUID(session_id))
        if session is None:
            raise ValueError("Interview session not found")

        # 读取消息记录
        messages = db.scalars(
            select(InterviewMessage)
            .where(InterviewMessage.session_id == session.id)
            .order_by(InterviewMessage.created_at.asc())
        ).all()

        if not messages:
            raise ValueError("No messages found for this session")

        message_dicts = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        agent = EvaluatorAgent(
            mode=session.mode,
            messages=message_dicts,
        )
        analysis = agent.analyze()

        scores = analysis.get("scores", {})
        report = InterviewReport(
            session_id=uuid.UUID(session_id),
            overall_score=analysis.get("overall_score", 0),
            scores={
                dim: scores.get(dim, 0)
                for dim in ("python_foundation", "backend_engineering", "database_understanding",
                            "agent_understanding", "project_depth", "communication")
            },
            strengths=analysis.get("strengths", []),
            weaknesses=analysis.get("weaknesses", []),
            suggestions=analysis.get("suggestions", []),
            recommended_topics=analysis.get("recommended_topics", []),
            improved_answers=analysis.get("improved_answers", []),
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
                "interview_report_id": str(report.id),
                "overall_score": report.overall_score,
            },
        )
        logger.info("Interview report %s generated, score=%d", report.id, report.overall_score)
        return {"interview_report_id": str(report.id)}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db, celery_task_id=self.request.id, status="failed", progress=100, error_message=str(exc)
        )
        raise
    finally:
        db.close()
