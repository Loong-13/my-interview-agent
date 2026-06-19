"""个人知识库业务逻辑。"""

import hashlib
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import AppError
from backend.app.models.knowledge import KnowledgeChunk, KnowledgeCollection, KnowledgeDocument, QuestionBankItem
from backend.app.schemas.knowledge import KnowledgeCollectionCreate, KnowledgeTextDocumentCreate
from backend.app.utils.embedding_client import cosine_similarity, embed_texts


def create_collection(db: Session, *, user_id: uuid.UUID, payload: KnowledgeCollectionCreate) -> KnowledgeCollection:
    # 集合是用户的资料分组，不和项目强绑定，方便多个求职项目复用。
    collection = KnowledgeCollection(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        visibility=payload.visibility.value,
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def list_collections(db: Session, *, user_id: uuid.UUID) -> list[KnowledgeCollection]:
    return list(
        db.scalars(
            select(KnowledgeCollection)
            .where(KnowledgeCollection.user_id == user_id)
            .order_by(KnowledgeCollection.created_at.desc())
        ).all()
    )


def get_collection_for_user(db: Session, *, collection_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeCollection:
    # 所有知识库入口都必须经过 user_id 限定，避免跨账号检索资料。
    collection = db.scalar(
        select(KnowledgeCollection).where(
            KnowledgeCollection.id == collection_id,
            KnowledgeCollection.user_id == user_id,
        )
    )
    if collection is None:
        raise AppError("KNOWLEDGE_COLLECTION_NOT_FOUND", "Knowledge collection not found", 404)
    return collection


def create_text_document(
    db: Session,
    *,
    user_id: uuid.UUID,
    collection_id: uuid.UUID,
    payload: KnowledgeTextDocumentCreate,
) -> KnowledgeDocument:
    get_collection_for_user(db, collection_id=collection_id, user_id=user_id)
    document = KnowledgeDocument(
        user_id=user_id,
        collection_id=collection_id,
        title=payload.title,
        file_type="text",
        content_type=payload.content_type.value,
        raw_text=payload.raw_text,
        document_metadata=payload.metadata,
        status="parsed",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def create_uploaded_document(
    db: Session,
    *,
    user_id: uuid.UUID,
    collection_id: uuid.UUID,
    title: str,
    file_name: str,
    file_url: str,
    file_type: str,
    content_type: str,
) -> KnowledgeDocument:
    get_collection_for_user(db, collection_id=collection_id, user_id=user_id)
    document = KnowledgeDocument(
        user_id=user_id,
        collection_id=collection_id,
        title=title,
        file_name=file_name,
        file_url=file_url,
        file_type=file_type,
        content_type=content_type,
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def list_documents(
    db: Session,
    *,
    user_id: uuid.UUID,
    collection_id: uuid.UUID | None = None,
) -> list[KnowledgeDocument]:
    stmt = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)
    if collection_id is not None:
        get_collection_for_user(db, collection_id=collection_id, user_id=user_id)
        stmt = stmt.where(KnowledgeDocument.collection_id == collection_id)
    return list(db.scalars(stmt.order_by(KnowledgeDocument.created_at.desc())).all())


def get_document_for_user(db: Session, *, document_id: uuid.UUID, user_id: uuid.UUID) -> KnowledgeDocument:
    document = db.scalar(
        select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id,
            KnowledgeDocument.user_id == user_id,
        )
    )
    if document is None:
        raise AppError("KNOWLEDGE_DOCUMENT_NOT_FOUND", "Knowledge document not found", 404)
    return document


def ensure_collections_belong_to_user(
    db: Session,
    *,
    collection_ids: list[uuid.UUID],
    user_id: uuid.UUID,
) -> None:
    # 空列表表示检索当前用户全部集合。
    for collection_id in collection_ids:
        get_collection_for_user(db, collection_id=collection_id, user_id=user_id)


def search_chunks(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str,
    collection_ids: list[uuid.UUID] | None = None,
    top_k: int = 5,
) -> list[tuple[KnowledgeChunk, float]]:
    ensure_collections_belong_to_user(db, collection_ids=collection_ids or [], user_id=user_id)
    query_embedding = embed_texts([query])[0]

    stmt = select(KnowledgeChunk).where(
        KnowledgeChunk.user_id == user_id,
        KnowledgeChunk.embedding.is_not(None),
    )
    if collection_ids:
        stmt = stmt.where(KnowledgeChunk.collection_id.in_(collection_ids))

    # MVP 先在应用层做相似度排序，避免测试环境必须依赖 pgvector 运算符。
    scored: list[tuple[KnowledgeChunk, float]] = []
    for chunk in db.scalars(stmt).all():
        if chunk.embedding:
            scored.append((chunk, cosine_similarity(query_embedding, chunk.embedding)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def search_question_bank_items(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str,
    collection_ids: list[uuid.UUID] | None = None,
    top_k: int = 5,
) -> list[QuestionBankItem]:
    ensure_collections_belong_to_user(db, collection_ids=collection_ids or [], user_id=user_id)
    terms = [term for term in query.lower().split() if term]
    stmt = select(QuestionBankItem).where(QuestionBankItem.user_id == user_id)
    if collection_ids:
        stmt = stmt.where(QuestionBankItem.collection_id.in_(collection_ids))
    items = list(db.scalars(stmt.order_by(QuestionBankItem.created_at.desc())).all())
    if not terms:
        return items[:top_k]

    def score(item: QuestionBankItem) -> int:
        text = " ".join(
            [
                item.question,
                item.reference_answer or "",
                " ".join(item.tags or []),
                item.type,
            ]
        ).lower()
        return sum(1 for term in terms if term in text)

    return [item for item in sorted(items, key=score, reverse=True) if score(item) > 0][:top_k]


def build_retrieval_query(
    *,
    focus: list[str] | None,
    match_report: dict[str, Any] | None,
    jd_analysis: dict[str, Any] | None,
    mode: str,
    difficulty: str,
) -> str:
    # 检索 query 优先体现用户主动 focus，其次补上报告短板和 JD 要求。
    parts: list[str] = []
    parts.extend(focus or [])
    if match_report:
        parts.extend(match_report.get("missing_skills") or [])
        parts.extend(match_report.get("interview_focus") or [])
    if jd_analysis:
        parts.extend(jd_analysis.get("required_skills") or [])
        parts.extend(jd_analysis.get("interview_topics") or [])
    parts.extend([mode, difficulty])
    return " ".join(str(part) for part in parts if part)


def make_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def infer_file_type(path: str) -> str:
    return Path(path).suffix.lower().removeprefix(".")
