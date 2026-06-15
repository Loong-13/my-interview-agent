import uuid

from backend.app.core.database import SessionLocal
from backend.app.models.match_report import MatchReport
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="match_report.generate")
def generate_match_report_task(
    self, project_id: str, resume_id: str, job_description_id: str
) -> dict[str, str]:
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        report = MatchReport(
            project_id=uuid.UUID(project_id),
            resume_id=uuid.UUID(resume_id),
            job_description_id=uuid.UUID(job_description_id),
            match_score=0,
            matched_skills=[],
            missing_skills=[],
            interview_focus=[],
            suggestions=["MatchAgent is not implemented yet"],
            raw_report={"prompt_version": "match_analysis_stub_v1"},
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"match_report_id": str(report.id)},
        )
        return {"match_report_id": str(report.id)}
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
