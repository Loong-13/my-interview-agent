"""聚合所有 v1 API 路由。"""

from fastapi import APIRouter

from backend.app.api.v1 import (
    auth,
    interviews,
    job_descriptions,
    knowledge,
    match_reports,
    projects,
    question_bank,
    questions,
    resumes,
    tasks,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(resumes.router, tags=["resumes"])
api_router.include_router(job_descriptions.router, tags=["job-descriptions"])
api_router.include_router(match_reports.router, tags=["match-reports"])
api_router.include_router(questions.router, tags=["questions"])
api_router.include_router(interviews.router, tags=["interviews"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(question_bank.router, prefix="/question-bank", tags=["question-bank"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
