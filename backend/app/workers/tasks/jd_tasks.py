import uuid

from backend.app.core.database import SessionLocal
from backend.app.models.job_description import JobDescription
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="jd.analyze")
def analyze_jd_task(self, job_description_id: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        jd = db.get(JobDescription, uuid.UUID(job_description_id))
        if jd is None:
            raise ValueError("Job description not found")

        # Placeholder until the real JDAnalyzerAgent is wired.
        jd.analysis_json = {
            "prompt_version": "jd_analysis_stub_v1",
            "direction": "unknown",
            "required_skills": [],
            "bonus_skills": [],
            "interview_topics": [],
        }
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"job_description_id": str(jd.id)},
        )
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
        raise
    finally:
        db.close()
