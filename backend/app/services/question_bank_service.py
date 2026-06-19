"""个人题库业务逻辑。"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppError
from backend.app.models.knowledge import QuestionBankItem, QuestionBankItemEmbedding
from backend.app.schemas.question_bank import QuestionBankImportRequest, QuestionBankItemCreate
from backend.app.services.knowledge_base_service import get_collection_for_user
from backend.app.utils.embedding_client import embed_texts, get_embedding_model_name


def create_question_bank_item(
    db: Session,
    *,
    user_id: uuid.UUID,
    payload: QuestionBankItemCreate,
    source: str = "manual",
) -> QuestionBankItem:
    # 题库条目可以不绑定集合，但绑定时必须确认集合属于当前用户。
    if payload.collection_id is not None:
        get_collection_for_user(db, collection_id=payload.collection_id, user_id=user_id)

    item = QuestionBankItem(
        user_id=user_id,
        collection_id=payload.collection_id,
        type=payload.type,
        difficulty=payload.difficulty,
        question=payload.question,
        reference_answer=payload.reference_answer,
        evaluation_points=payload.evaluation_points,
        tags=payload.tags,
        source=source,
    )
    db.add(item)
    db.flush()
    _create_item_embedding(db, item)
    db.commit()
    db.refresh(item)
    return item


def list_question_bank_items(
    db: Session,
    *,
    user_id: uuid.UUID,
    collection_id: uuid.UUID | None = None,
    type_: str | None = None,
    difficulty: str | None = None,
    tag: str | None = None,
    keyword: str | None = None,
) -> list[QuestionBankItem]:
    stmt = select(QuestionBankItem).where(QuestionBankItem.user_id == user_id)
    if collection_id is not None:
        get_collection_for_user(db, collection_id=collection_id, user_id=user_id)
        stmt = stmt.where(QuestionBankItem.collection_id == collection_id)
    if type_:
        stmt = stmt.where(QuestionBankItem.type == type_)
    if difficulty:
        stmt = stmt.where(QuestionBankItem.difficulty == difficulty)

    items = list(db.scalars(stmt.order_by(QuestionBankItem.created_at.desc())).all())
    if tag:
        items = [item for item in items if tag in (item.tags or [])]
    if keyword:
        lowered = keyword.lower()
        items = [
            item
            for item in items
            if lowered in item.question.lower() or lowered in (item.reference_answer or "").lower()
        ]
    return items


def import_question_bank_items(
    db: Session,
    *,
    user_id: uuid.UUID,
    payload: QuestionBankImportRequest,
) -> list[QuestionBankItem]:
    get_collection_for_user(db, collection_id=payload.collection_id, user_id=user_id)
    if payload.format != "qa_markdown":
        raise AppError("UNSUPPORTED_IMPORT_FORMAT", "Only qa_markdown import is supported")

    pairs = parse_qa_markdown(payload.content)
    if not pairs:
        raise AppError("NO_QUESTIONS_PARSED", "No Q/A items parsed from content")

    items: list[QuestionBankItem] = []
    for question, answer in pairs:
        item = QuestionBankItem(
            user_id=user_id,
            collection_id=payload.collection_id,
            type="question_bank_review",
            difficulty="intern",
            question=question,
            reference_answer=answer,
            evaluation_points=[],
            tags=[],
            source="imported",
        )
        db.add(item)
        db.flush()
        _create_item_embedding(db, item)
        items.append(item)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


def parse_qa_markdown(content: str) -> list[tuple[str, str]]:
    # 支持常见的 Q/A、问题/答案格式，先满足八股文导入的高频场景。
    pattern = re.compile(
        r"(?:^|\n)\s*(?:Q[:：]|问题[:：])\s*(?P<q>.+?)\n\s*(?:A[:：]|答案[:：])\s*(?P<a>.*?)(?=\n\s*(?:Q[:：]|问题[:：])|\Z)",
        re.S,
    )
    pairs: list[tuple[str, str]] = []
    for match in pattern.finditer(content.strip()):
        question = re.sub(r"\s+", " ", match.group("q")).strip()
        answer = match.group("a").strip()
        if question:
            pairs.append((question, answer))
    return pairs


def _create_item_embedding(db: Session, item: QuestionBankItem) -> None:
    embedding_text = " ".join(
        [
            item.question,
            item.reference_answer or "",
            " ".join(item.tags or []),
            item.type,
            item.difficulty,
        ]
    )
    embedding = embed_texts([embedding_text])[0]
    db.add(
        QuestionBankItemEmbedding(
            question_bank_item_id=item.id,
            embedding_text=embedding_text,
            embedding=embedding,
            embedding_model=get_embedding_model_name(),
        )
    )
