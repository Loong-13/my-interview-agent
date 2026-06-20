"""个人知识库索引和题库导入异步任务。"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.schemas.question_bank import QuestionBankImportRequest
from app.services.knowledge_base_service import make_content_hash
from app.services.question_bank_service import import_question_bank_items, parse_qa_markdown
from app.services.task_service import update_task_status
from app.utils.document_parser import parse_document_text
from app.utils.embedding_client import embed_texts, get_embedding_model_name
from app.utils.text_chunker import clean_text, split_text_into_chunks
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="knowledge_document.index")
def index_knowledge_document_task(self, document_id: str, extract_questions: bool = False) -> dict[str, object]:
    """解析并索引个人知识库文档。"""
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=5)
        document = db.get(KnowledgeDocument, uuid.UUID(document_id))
        if document is None:
            raise ValueError("Knowledge document not found")

        # 文档可能是上传文件，也可能是粘贴文本；两者最终都归一到 raw_text。
        document.status = "parsing"
        document.parse_error = None
        db.commit()

        raw_text = document.raw_text
        if not raw_text:
            if not document.file_url:
                raise ValueError("Document has neither raw_text nor file_url")
            raw_text = parse_document_text(document.file_url, document.file_type)
            document.raw_text = raw_text
        document.status = "parsed"
        db.commit()
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=25)

        # 重新索引时先清理旧 chunk，保证 chunk_index 和 chunk_count 一致。
        document.status = "chunking"
        cleaned = clean_text(raw_text or "")
        chunks = split_text_into_chunks(cleaned)
        db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.document_id == document.id))
        db.commit()
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=45)

        document.status = "embedding"
        embedding_inputs = [
            f"标题：{document.title}\n章节：{chunk.title or ''}\n类型：{document.content_type}\n内容：{chunk.content}"
            for chunk in chunks
        ]
        embeddings = embed_texts(embedding_inputs) if embedding_inputs else []
        embedding_model = get_embedding_model_name()

        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            db.add(
                KnowledgeChunk(
                    user_id=document.user_id,
                    collection_id=document.collection_id,
                    document_id=document.id,
                    chunk_index=index,
                    title=chunk.title,
                    content=chunk.content,
                    token_count=len(chunk.content),
                    embedding=embedding,
                    embedding_model=embedding_model,
                    content_hash=make_content_hash(chunk.content),
                    chunk_metadata=chunk.metadata,
                )
            )

        question_count = 0
        if extract_questions and document.collection_id:
            # 自动抽题只处理明显 Q/A 格式，避免强行从普通段落造题。
            for question, answer in parse_qa_markdown(cleaned):
                from app.models.knowledge import QuestionBankItem

                db.add(
                    QuestionBankItem(
                        user_id=document.user_id,
                        collection_id=document.collection_id,
                        document_id=document.id,
                        type="question_bank_review",
                        difficulty="intern",
                        question=question,
                        reference_answer=answer,
                        evaluation_points=[],
                        tags=[],
                        source="document_extract",
                        quality_score=70,
                    )
                )
                question_count += 1

        document.status = "indexed"
        document.chunk_count = len(chunks)
        document.indexed_at = datetime.now(UTC)
        db.commit()
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={
                "document_id": str(document.id),
                "chunk_count": len(chunks),
                "question_count": question_count,
            },
        )
        logger.info("Indexed knowledge document %s with %d chunks", document.id, len(chunks))
        return {"document_id": str(document.id), "chunk_count": len(chunks)}
    except Exception as exc:
        db.rollback()
        document = db.get(KnowledgeDocument, uuid.UUID(document_id))
        if document is not None:
            document.status = "failed"
            document.parse_error = str(exc)
            db.commit()
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


@celery_app.task(bind=True, name="question_bank.import")
def import_question_bank_task(
    self,
    user_id: str,
    collection_id: str,
    format: str,
    content: str,
) -> dict[str, object]:
    """批量导入个人题库。"""
    db = SessionLocal()
    try:
        update_task_status(db, celery_task_id=self.request.id, status="running", progress=10)
        items = import_question_bank_items(
            db,
            user_id=uuid.UUID(user_id),
            payload=QuestionBankImportRequest(
                collection_id=uuid.UUID(collection_id),
                format=format,
                content=content,
            ),
        )
        item_ids = [str(item.id) for item in items]
        update_task_status(
            db,
            celery_task_id=self.request.id,
            status="success",
            progress=100,
            result_json={"item_ids": item_ids, "count": len(item_ids)},
        )
        return {"item_ids": item_ids, "count": len(item_ids)}
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
