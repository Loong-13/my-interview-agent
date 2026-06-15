import uuid

from backend.app.core.database import SessionLocal
from backend.app.models.interview import InterviewReport
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="interview_report.generate")
def generate_interview_report_task(self, session_id: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        report = InterviewReport(
            session_id=uuid.UUID(session_id),
            overall_score=0,
            scores={
                "python_foundation": 0,
                "backend_engineering": 0,
                "database_understanding": 0,
                "agent_understanding": 0,
                "project_depth": 0,
                "communication": 0,
            },
            strengths=[],
            weaknesses=["EvaluatorAgent is not implemented yet"],
            suggestions=["Wire EvaluatorAgent to generate structured interview reports"],
            recommended_topics=[],
            improved_answers=[],
            raw_report={"prompt_version": "evaluator_stub_v1"},
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"interview_report_id": str(report.id)},
        )
        return {"interview_report_id": str(report.id)}
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
