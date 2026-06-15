import uuid

from backend.app.core.database import SessionLocal
from backend.app.models.question import Question
from backend.app.services.task_service import update_task_status
from backend.app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="questions.generate")
def generate_questions_task(
    self,
    project_id: str,
    mode: str,
    difficulty: str,
    count: int,
    focus: list[str] | None = None,
) -> dict[str, object]:
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        focus_text = "、".join(focus or []) or "Python 后端 / Agent 基础"
        questions: list[Question] = []
        for index in range(count):
            questions.append(
                Question(
                    project_id=uuid.UUID(project_id),
                    type=mode,
                    difficulty=difficulty,
                    question=f"[占位题 {index + 1}] 请说明你对 {focus_text} 的理解。",
                    evaluation_points=["概念准确性", "项目结合度", "表达结构"],
                    source="stub",
                )
            )
        db.add_all(questions)
        db.commit()
        question_ids = [str(question.id) for question in questions]
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"question_ids": question_ids},
        )
        return {"question_ids": question_ids}
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
