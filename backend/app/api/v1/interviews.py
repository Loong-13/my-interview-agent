"""面试会话接口与报告生成触发器。"""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppError
from backend.app.models.interview import InterviewMessage, InterviewReport, InterviewSession
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewCreate,
    InterviewCreateResponse,
    InterviewMessageResponse,
    InterviewReportResponse,
    InterviewStartResponse,
)
from backend.app.services.project_service import get_project_for_user
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.interview_tasks import generate_interview_report_task

router = APIRouter()


@router.post("/projects/{project_id}/interviews", response_model=InterviewCreateResponse)
def create_interview(
    project_id: uuid.UUID,
    payload: InterviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewCreateResponse:
    # 创建一个绑定到用户项目的面试会话。
    project = get_project_for_user(db, project_id, current_user.id)
    session = InterviewSession(
        project_id=project.id,
        mode=payload.mode.value,
        difficulty=payload.difficulty,
        status="created",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return InterviewCreateResponse(session_id=session.id, status=session.status)


@router.post("/interviews/{session_id}/start", response_model=InterviewStartResponse)
def start_interview(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewStartResponse:
    # 启动会话时记录开始时间，并写入第一条面试官提问。
    session = _get_session_for_user(db, session_id, current_user.id)
    session.status = "running"
    session.started_at = datetime.now(UTC)
    first_question = "请先介绍一下你做过的一个 Python 后端或 Agent 项目。"
    message = InterviewMessage(session_id=session.id, role="interviewer", content=first_question)
    db.add(message)
    db.commit()
    return InterviewStartResponse(session_id=session.id, first_question=first_question)


@router.post("/interviews/{session_id}/answers", response_model=InterviewAnswerResponse)
def submit_answer(
    session_id: uuid.UUID,
    payload: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewAnswerResponse:
    # 当前实现会保存对话消息，并返回固定的追问占位逻辑。
    session = _get_session_for_user(db, session_id, current_user.id)
    candidate_message = InterviewMessage(
        session_id=session.id,
        role="candidate",
        content=payload.answer,
    )
    feedback = "回答已记录。当前是占位面试官逻辑，后续会接入 InterviewerAgent。"
    next_question = "请进一步说明这个项目中的技术难点，以及你具体如何解决。"
    interviewer_message = InterviewMessage(
        session_id=session.id,
        role="interviewer",
        content=next_question,
        feedback_json={"feedback": feedback, "prompt_version": "interviewer_stub_v1"},
    )
    db.add_all([candidate_message, interviewer_message])
    db.commit()
    return InterviewAnswerResponse(
        feedback=feedback,
        next_question=next_question,
        should_continue=True,
    )


@router.post("/interviews/{session_id}/finish", response_model=dict[str, str])
def finish_interview(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    # 标记会话完成，便于后续报告生成使用完整 transcript。
    session = _get_session_for_user(db, session_id, current_user.id)
    session.status = "completed"
    session.ended_at = datetime.now(UTC)
    db.commit()
    return {"session_id": str(session.id), "status": session.status}


@router.post("/interviews/{session_id}/report", response_model=TaskAccepted)
def generate_report(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 报告生成可能调用 LLM，因此有意设计为异步任务。
    session = _get_session_for_user(db, session_id, current_user.id)
    celery_result = generate_interview_report_task.delay(str(session.id))
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=session.project_id,
        celery_task_id=celery_result.id,
        task_type="interview_report.generate",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.get("/interviews/{session_id}/messages", response_model=list[InterviewMessageResponse])
def get_messages(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[InterviewMessageResponse]:
    # 前端通过持久化消息回放完整对话。
    session = _get_session_for_user(db, session_id, current_user.id)
    messages = db.scalars(
        select(InterviewMessage)
        .where(InterviewMessage.session_id == session.id)
        .order_by(InterviewMessage.created_at.asc())
    ).all()
    return [InterviewMessageResponse.model_validate(message) for message in messages]


@router.get("/interviews/{session_id}/report", response_model=InterviewReportResponse)
def get_report(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InterviewReport:
    # 报告查询和生成分离，方便客户端轮询生成结果。
    session = _get_session_for_user(db, session_id, current_user.id)
    report = db.scalar(select(InterviewReport).where(InterviewReport.session_id == session.id))
    if report is None:
        raise AppError("REPORT_NOT_FOUND", "Interview report not found", status_code=404)
    return report


def _get_session_for_user(db: Session, session_id: uuid.UUID, user_id: uuid.UUID) -> InterviewSession:
    # 复用项目归属校验，防止跨账号访问面试会话。
    session = db.get(InterviewSession, session_id)
    if session is None:
        raise AppError("INTERVIEW_NOT_FOUND", "Interview session not found", status_code=404)
    get_project_for_user(db, session.project_id, user_id)
    return session

