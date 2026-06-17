"""面试题批量生成任务。"""

import logging
import uuid

from backend.app.agents.question_generator_agent import QuestionGeneratorAgent
from backend.app.core.database import SessionLocal
from backend.app.models.match_report import MatchReport
from backend.app.models.project import Project
from backend.app.models.question import Question
from backend.app.models.resume import Resume
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="questions.generate")
def generate_questions_task(
    self,
    project_id: str,
    mode: str,
    difficulty: str,
    count: int,
    focus: list[str] | None = None,
) -> dict[str, object]:
    """调用 QuestionGeneratorAgent 批量生成面试题。

    流程：
    1. 读取项目下的简历分析、JD 分析、最新匹配报告
    2. 调用 QuestionGeneratorAgent.analyze()
    3. 批量写入 questions 表
    """
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)

        project = db.get(Project, uuid.UUID(project_id))
        if project is None:
            raise ValueError("Project not found")

        # 收集项目上下文
        resume_analysis: dict | None = None
        resume = db.query(Resume).filter(
            Resume.project_id == uuid.UUID(project_id)
        ).order_by(Resume.created_at.desc()).first()
        if resume:
            resume_analysis = resume.analysis_json

        jd_analysis: dict | None = None
        match_report: dict | None = None
        if resume:
            match = (
                db.query(MatchReport)
                .filter(MatchReport.project_id == uuid.UUID(project_id))
                .order_by(MatchReport.created_at.desc())
                .first()
            )
            if match:
                match_report = {
                    "match_score": match.match_score,
                    "matched_skills": match.matched_skills,
                    "missing_skills": match.missing_skills,
                    "interview_focus": match.interview_focus,
                }

        agent = QuestionGeneratorAgent(
            mode=mode,
            difficulty=difficulty,
            count=count,
            resume_analysis=resume_analysis,
            jd_analysis=jd_analysis,
            match_report=match_report,
        )
        analysis = agent.analyze()

        # 批量写入题目
        questions: list[Question] = []
        for q in analysis.get("questions", []):
            questions.append(
                Question(
                    project_id=uuid.UUID(project_id),
                    type=q.get("type", mode),
                    difficulty=q.get("difficulty", difficulty),
                    question=q.get("question", ""),
                    reference_answer=q.get("reference_answer"),
                    evaluation_points=q.get("evaluation_points", []),
                    source="ai_generated",
                )
            )

        if not questions:
            raise ValueError("QuestionGeneratorAgent produced no questions")

        db.add_all(questions)
        db.commit()
        question_ids = [str(q.id) for q in questions]
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"question_ids": question_ids, "count": len(question_ids)},
        )
        logger.info("Generated %d questions for project %s", len(questions), project_id)
        return {"question_ids": question_ids}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db, celery_task_id=self.request.id, status="failed", progress=100, error_message=str(exc)
        )
        raise
    finally:
        db.close()
