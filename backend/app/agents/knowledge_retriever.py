"""知识检索器 — 为 Agent 提示词提供个人知识库 RAG 检索能力。

本模块不是 LLM Agent（不继承 BaseLLMAgent），而是对知识库检索流程的封装。
其他 Agent（QuestionGenerator、Interviewer、Evaluator 等）在构造 prompt 前
调用本模块的 retrieve_context() 获取知识上下文，实现检索增强生成。

整体链路：
  用户 query / 系统自动构造的 query
    → 调用 embedding_client 生成查询向量
    → pgvector 或应用层余弦相似度搜索 KnowledgeChunk
    → 对召回结果进行去重、排序、截断
    → 格式化为可直接拼接进 Agent prompt 的文本片段
"""

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.services.knowledge_base_service import (
    build_retrieval_query,
    search_chunks,
    search_question_bank_items,
)

logger = logging.getLogger(__name__)

# 单次检索最多返回的 chunk 数量，避免提示词过长。
DEFAULT_TOP_K = 5
# 格式化时每个 chunk 的最大字符数，超过部分截断并标注省略。
MAX_CHUNK_CONTENT_LENGTH = 800
# 检索召回分数低于此值的 chunk 会被过滤，减少噪音干扰。
MIN_SCORE_THRESHOLD = 0.15


def retrieve_context(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str | None = None,
    collection_ids: list[uuid.UUID] | None = None,
    focus: list[str] | None = None,
    match_report: dict[str, Any] | None = None,
    jd_analysis: dict[str, Any] | None = None,
    mode: str = "",
    difficulty: str = "",
    top_k: int = DEFAULT_TOP_K,
    include_question_bank: bool = False,
) -> str:
    """检索知识库上下文，返回可直接拼入 Agent prompt 的文本片段。

    这是外部调用的主入口。支持两种查询来源：
    1. 直接传入 query，用于用户主动搜索的场景。
    2. 通过 focus / match_report / jd_analysis 等结构化字段自动构造查询，
       用于面试题生成、模拟追问等 Agent 自动增强场景。

    参数
    ----------
    db : Session
        SQLAlchemy 数据库会话。
    user_id : uuid.UUID
        当前用户 ID，检索限定在用户自己的资料范围内。
    query : str | None
        直接指定的检索查询字符串，优先级高于自动构造。
    collection_ids : list[uuid.UUID] | None
        限定在指定集合内检索，None 或空列表表示检索所有集合。
    focus : list[str] | None
        用户主动指定的关注方向（如 ["Python异步", "FastAPI中间件"]）。
    match_report : dict[str, Any] | None
        简历-JD 匹配报告，含 missing_skills / interview_focus。
    jd_analysis : dict[str, Any] | None
        JD 分析结果，含 required_skills / interview_topics。
    mode : str
        面试题模式（如 "rag_project_deep_dive" / "fundamental"）。
    difficulty : str
        难度等级（如 "intern" / "junior" / "mid"）。
    top_k : int
        返回的 chunk 数量上限，默认 5。
    include_question_bank : bool
        是否同时检索个人题库，默认关闭以节省 token。

    返回
    -------
    str
        格式化的上下文文本，可直接拼接到 LLM prompt 中。
        无检索结果时返回空字符串。
    """
    # 1. 构造或使用传入的检索查询
    retrieval_query = _resolve_query(
        query=query,
        focus=focus,
        match_report=match_report,
        jd_analysis=jd_analysis,
        mode=mode,
        difficulty=difficulty,
    )

    if not retrieval_query.strip():
        logger.info("知识检索 query 为空，跳过。")
        return ""

    logger.info("知识检索 query=%r collection_ids=%s top_k=%d", retrieval_query, collection_ids, top_k)

    # 2. 从知识块表检索
    chunk_results = search_chunks(
        db,
        user_id=user_id,
        query=retrieval_query,
        collection_ids=collection_ids,
        top_k=top_k * 2,  # 多召回一些，后续质量过滤后再截断
    )

    # 3. 质量过滤：去掉得分过低的噪音结果
    filtered = [(chunk, score) for chunk, score in chunk_results if score >= MIN_SCORE_THRESHOLD]

    # 4. 格式化为 prompt 上下文
    context_parts = format_retrieved_chunks(filtered, top_k=top_k)

    # 5. 可选：附带个人题库中匹配的结构化题目
    if include_question_bank:
        question_bank_part = _retrieve_question_bank_context(
            db,
            user_id=user_id,
            query=retrieval_query,
            collection_ids=collection_ids,
            top_k=top_k,
        )
        if question_bank_part:
            context_parts.append(question_bank_part)

    return "\n\n".join(context_parts) if context_parts else ""


def retrieve_chunks_raw(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str,
    collection_ids: list[uuid.UUID] | None = None,
    top_k: int = DEFAULT_TOP_K,
    min_score: float = MIN_SCORE_THRESHOLD,
) -> list[dict[str, Any]]:
    """检索知识块原始数据，返回结构化列表，供需要自行处理的调用方使用。

    参数
    ----------
    db : Session
        数据库会话。
    user_id : uuid.UUID
        用户 ID。
    query : str
        检索查询字符串，必须由调用方提供。
    collection_ids : list[uuid.UUID] | None
        限定集合，None 表示全量检索。
    top_k : int
        返回数量上限。
    min_score : float
        最低相似度阈值，低于此分数的结果会被丢弃。

    返回
    -------
    list[dict[str, Any]]
        每个元素包含 chunk_id / document_id / title / content / score / metadata。
    """
    results = search_chunks(
        db,
        user_id=user_id,
        query=query,
        collection_ids=collection_ids,
        top_k=top_k * 2,
    )
    return [
        {
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "title": chunk.title or "",
            "content": chunk.content,
            "score": round(score, 4),
            "metadata": chunk.chunk_metadata or {},
        }
        for chunk, score in results
        if score >= min_score
    ][:top_k]


def format_retrieved_chunks(
    scored_chunks: list[tuple[Any, float]],
    top_k: int = DEFAULT_TOP_K,
) -> list[str]:
    """将检索召回的 chunk 列表格式化为 LLM prompt 可直接使用的文本片段。

    每个 chunk 格式化为：
      [资料#N | 标题 | 相似度: X.XX]
      正文内容（最多 800 字符，超出截断并标注）

    参数
    ----------
    scored_chunks : list[tuple[KnowledgeChunk, float]]
        由 search_chunks 返回的 (chunk, score) 元组列表。
    top_k : int
        最终保留的 chunk 数量，默认 5。

    返回
    -------
    list[str]
        每个元素是一段格式化的 chunk 文本，可按需合并或逐条使用。
    """
    if not scored_chunks:
        return []

    context_lines: list[str] = []
    context_lines.append("【以下内容来自个人知识库，可用于增强回答的技术深度】")

    for index, (chunk, score) in enumerate(scored_chunks[:top_k], start=1):
        title = chunk.title or "无标题"
        content = chunk.content or ""

        # 限制单块内容长度，避免 prompt 膨胀
        if len(content) > MAX_CHUNK_CONTENT_LENGTH:
            content = content[:MAX_CHUNK_CONTENT_LENGTH] + "\n...（内容过长，已截断）"

        chunk_text = (
            f"[资料#{index} | {title} | 相似度: {score:.2f}]\n"
            f"{content}"
        )
        context_lines.append(chunk_text)

    return context_lines


def _resolve_query(
    *,
    query: str | None,
    focus: list[str] | None,
    match_report: dict[str, Any] | None,
    jd_analysis: dict[str, Any] | None,
    mode: str,
    difficulty: str,
) -> str:
    """决定最终的检索查询字符串。

    优先级：直接传入的 query > 自动构造的 retrieval_query。
    """
    if query is not None:
        return query.strip()

    # 从结构化上下文中自动构造检索查询
    return build_retrieval_query(
        focus=focus,
        match_report=match_report,
        jd_analysis=jd_analysis,
        mode=mode,
        difficulty=difficulty,
    )


def _retrieve_question_bank_context(
    db: Session,
    *,
    user_id: uuid.UUID,
    query: str,
    collection_ids: list[uuid.UUID] | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> str | None:
    """检索个人题库中匹配的结构化题目，格式化为提示词上下文。

    参数
    ----------
    db : Session
        数据库会话。
    user_id : uuid.UUID
        用户 ID。
    query : str
        检索查询（用于关键词匹配）。
    collection_ids : list[uuid.UUID] | None
        限定集合。
    top_k : int
        返回题目数量上限。

    返回
    -------
    str | None
        格式化的题库上下文文本，无匹配时返回 None。
    """
    items = search_question_bank_items(
        db,
        user_id=user_id,
        query=query,
        collection_ids=collection_ids,
        top_k=top_k,
    )

    if not items:
        return None

    lines: list[str] = []
    lines.append("【以下内容来自个人题库，可用于参考回答要点】")

    for index, item in enumerate(items[:top_k], start=1):
        question = item.question or "无题目"
        tags = "、".join(item.tags) if item.tags else "无标签"
        reference = item.reference_answer or "无参考答案"

        # 参考答案如果太长也截断
        if len(reference) > MAX_CHUNK_CONTENT_LENGTH:
            reference = reference[:MAX_CHUNK_CONTENT_LENGTH] + "\n...（内容过长，已截断）"

        item_text = (
            f"[题库#{index} | {item.type} | 标签: {tags}]\n"
            f"题目: {question}\n"
            f"参考答案: {reference}"
        )
        lines.append(item_text)

    return "\n\n".join(lines)
