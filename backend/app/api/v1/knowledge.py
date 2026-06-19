"""个人知识库集合、文档和检索接口。"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.exceptions import AppError
from backend.app.models.user import User
from backend.app.schemas.common import TaskAccepted
from backend.app.schemas.knowledge import (
    KnowledgeCollectionCreate,
    KnowledgeCollectionListResponse,
    KnowledgeCollectionResponse,
    KnowledgeContentType,
    KnowledgeDocumentIndexRequest,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentUploadResponse,
    KnowledgeSearchItem,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeTextDocumentCreate,
)
from backend.app.services.knowledge_base_service import (
    create_collection,
    create_text_document,
    create_uploaded_document,
    get_document_for_user,
    list_collections,
    list_documents,
    search_chunks,
)
from backend.app.services.task_service import create_async_task
from backend.app.workers.tasks.knowledge_tasks import index_knowledge_document_task

router = APIRouter()


@router.post("/collections", response_model=KnowledgeCollectionResponse)
def create_knowledge_collection(
    payload: KnowledgeCollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeCollectionResponse:
    # 集合只归属于当前用户，是后续文档和题库的容器。
    collection = create_collection(db, user_id=current_user.id, payload=payload)
    return KnowledgeCollectionResponse.model_validate(collection)


@router.get("/collections", response_model=KnowledgeCollectionListResponse)
def get_knowledge_collections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeCollectionListResponse:
    collections = list_collections(db, user_id=current_user.id)
    return KnowledgeCollectionListResponse(
        items=[KnowledgeCollectionResponse.model_validate(collection) for collection in collections],
        total=len(collections),
    )


@router.post("/collections/{collection_id}/documents", response_model=KnowledgeDocumentUploadResponse)
def upload_knowledge_document(
    collection_id: uuid.UUID,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    content_type: KnowledgeContentType = Form(default=KnowledgeContentType.interview_notes),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentUploadResponse:
    # 文件上传只落盘和建记录，解析与索引交给 Celery。
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md", ".markdown"}:
        raise AppError("UNSUPPORTED_FILE_TYPE", "Only PDF, DOCX, TXT, and Markdown are supported")

    content = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise AppError("FILE_TOO_LARGE", "Uploaded file is too large")

    upload_dir = Path(settings.upload_dir) / "knowledge" / str(current_user.id) / str(collection_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}{suffix}"
    file_path.write_bytes(content)

    document = create_uploaded_document(
        db,
        user_id=current_user.id,
        collection_id=collection_id,
        title=title or file.filename or "Untitled",
        file_name=file.filename or file_path.name,
        file_url=str(file_path),
        file_type=suffix.removeprefix("."),
        content_type=content_type.value,
    )
    return KnowledgeDocumentUploadResponse(document_id=document.id, status=document.status)


@router.post("/collections/{collection_id}/documents/text", response_model=KnowledgeDocumentUploadResponse)
def create_knowledge_text_document(
    collection_id: uuid.UUID,
    payload: KnowledgeTextDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentUploadResponse:
    # 粘贴文本已经具备 raw_text，可直接进入 parsed 状态，等待索引任务切分和向量化。
    document = create_text_document(db, user_id=current_user.id, collection_id=collection_id, payload=payload)
    return KnowledgeDocumentUploadResponse(document_id=document.id, status=document.status)


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
def get_knowledge_documents(
    collection_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeDocumentListResponse:
    documents = list_documents(db, user_id=current_user.id, collection_id=collection_id)
    return KnowledgeDocumentListResponse(
        items=[KnowledgeDocumentResponse.model_validate(document) for document in documents],
        total=len(documents),
    )


@router.post("/documents/{document_id}/index", response_model=TaskAccepted)
def index_knowledge_document(
    document_id: uuid.UUID,
    payload: KnowledgeDocumentIndexRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskAccepted:
    # 索引任务包括解析、清洗、切分和 embedding，必须异步执行。
    document = get_document_for_user(db, document_id=document_id, user_id=current_user.id)
    celery_result = index_knowledge_document_task.delay(str(document.id), bool(payload and payload.extract_questions))
    task = create_async_task(
        db,
        user_id=current_user.id,
        project_id=None,
        celery_task_id=celery_result.id,
        task_type="knowledge_document.index",
    )
    return TaskAccepted(task_id=task.id, status=task.status)


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeSearchResponse:
    # 检索必须限定当前用户和可选集合，防止跨账号资料泄露。
    results = search_chunks(
        db,
        user_id=current_user.id,
        query=payload.query,
        collection_ids=payload.collection_ids,
        top_k=payload.top_k,
    )
    return KnowledgeSearchResponse(
        items=[
            KnowledgeSearchItem(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                title=chunk.title,
                content=chunk.content,
                score=score,
                metadata=chunk.chunk_metadata or {},
            )
            for chunk, score in results
        ]
    )
