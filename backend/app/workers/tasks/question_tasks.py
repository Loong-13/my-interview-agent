"""面试题批量生成任务。"""

import logging
import uuid
from typing import Any

from backend.app.agents.question_generator_agent import QuestionGeneratorAgent
from backend.app.core.database import SessionLocal
from backend.app.models.job_description import JobDescription
from backend.app.models.match_report import MatchReport
from backend.app.models.project import Project
from backend.app.models.question import Question
from backend.app.models.resume import Resume
from backend.app.services.knowledge_base_service import (
    build_retrieval_query,
    search_chunks,
    search_question_bank_items,
)
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
    """调用 QuestionGeneratorAgent 批量生成面试题。"""
    return _generate_questions(
        self,
        project_id=project_id,
        mode=mode,
        difficulty=difficulty,
        count=count,
        focus=focus,
        user_id=None,
        collection_ids=None,
    )


@celery_app.task(bind=True, name="questions.generate_from_knowledge")
def generate_questions_from_knowledge_task(
    self,
    project_id: str,
    user_id: str,
    mode: str,
    difficulty: str,
    count: int,
    collection_ids: list[str] | None = None,
    focus: list[str] | None = None,
) -> dict[str, object]:
    """结合个人知识库检索结果生成面试题。"""
    return _generate_questions(
        self,
        project_id=project_id,
        mode=mode,
        difficulty=difficulty,
        count=count,
        focus=focus,
        user_id=user_id,
        collection_ids=collection_ids,
    )


def _generate_questions(
    task_self: Any,
    *,
    project_id: str,
    mode: str,
    difficulty: str,
    count: int,
    focus: list[str] | None,
    user_id: str | None,
    collection_ids: list[str] | None,
) -> dict[str, object]:
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=task_self.request.id, status="running", progress=10)

        project_uuid = uuid.UUID(project_id)
        project = db.get(Project, project_uuid)
        if project is None:
            raise ValueError("Project not found")

        resume_analysis, jd_analysis, match_report = _load_project_context(db, project_uuid)
        retrieved_knowledge: list[dict[str, Any]] = []
        question_bank_items: list[dict[str, Any]] = []

        if user_id is not None:
            # 知识库增强模式先构造检索 query，再分别召回 chunk 和结构化题目。
            query = build_retrieval_query(
                focus=focus,
                match_report=match_report,
                jd_analysis=jd_analysis,
                mode=mode,
                difficulty=difficulty,
            )
            user_uuid = uuid.UUID(user_id)
            collection_uuids = [uuid.UUID(value) for value in collection_ids or []]
            chunk_results = search_chunks(
                db,
                user_id=user_uuid,
                query=query,
                collection_ids=collection_uuids,
                top_k=8,
            )
            retrieved_knowledge = [
                {
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "content": chunk.content,
                    "score": score,
                    "metadata": chunk.chunk_metadata,
                }
                for chunk, score in chunk_results
            ]
            items = search_question_bank_items(
                db,
                user_id=user_uuid,
                query=query,
                collection_ids=collection_uuids,
                top_k=8,
            )
            question_bank_items = [
                {
                    "id": str(item.id),
                    "question": item.question,
                    "reference_answer": item.reference_answer,
                    "tags": item.tags,
                }
                for item in items
            ]
            update_task_status(db, celery_task_id=task_self.request.id, status="running", progress=35)

        agent = QuestionGeneratorAgent(
            mode=mode,
            difficulty=difficulty,
            count=count,
            resume_analysis=resume_analysis,
            jd_analysis=jd_analysis,
            match_report=match_report,
            retrieved_knowledge=retrieved_knowledge,
            question_bank_items=question_bank_items,
        )
        analysis = agent.analyze()

        # 批量写入题目，并保留知识库来源，方便前端展示证据。
        questions: list[Question] = []
        for q in analysis.get("questions", []):
            source_refs = [str(ref) for ref in q.get("source_refs", [])]
            questions.append(
                Question(
                    project_id=project_uuid,
                    type=q.get("type", mode),
                    difficulty=q.get("difficulty", difficulty),
                    question=q.get("question", ""),
                    reference_answer=q.get("reference_answer"),
                    evaluation_points=q.get("evaluation_points", []),
                    source_chunk_ids=source_refs,
                    source="mixed" if user_id is not None else "ai_generated",
                )
            )

        if not questions:
            raise ValueError("QuestionGeneratorAgent produced no questions")

        db.add_all(questions)
        db.commit()
        question_ids = [str(q.id) for q in questions]
        update_task_status(
            db,
            celery_task_id=task_self.request.id,
            status="success",
            progress=100,
            result_json={"question_ids": question_ids, "count": len(question_ids)},
        )
        logger.info("Generated %d questions for project %s", len(questions), project_id)
        return {"question_ids": question_ids}
    except Exception as exc:
        db.rollback()
        update_task_status(
            db,
            celery_task_id=task_self.request.id,
            status="failed",
            progress=100,
            error_message=str(exc),
        )
        raise
    finally:
        db.close()


def _load_project_context(db, project_id: uuid.UUID) -> tuple[dict | None, dict | None, dict | None]:
    # 统一读取项目上下文，普通出题和知识库出题共用，避免两条链路不一致。
    resume_analysis: dict | None = None
    resume = db.query(Resume).filter(Resume.project_id == project_id).order_by(Resume.created_at.desc()).first()
    if resume:
        resume_analysis = resume.analysis_json

    jd_analysis: dict | None = None
    jd = (
        db.query(JobDescription)
        .filter(JobDescription.project_id == project_id)
        .order_by(JobDescription.created_at.desc())
        .first()
    )
    if jd:
        jd_analysis = jd.analysis_json

    match_report: dict | None = None
    match = (
        db.query(MatchReport)
        .filter(MatchReport.project_id == project_id)
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
    return resume_analysis, jd_analysis, match_report
