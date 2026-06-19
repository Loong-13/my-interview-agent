"""知识库文档切分工具。"""

import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    title: str | None
    content: str
    metadata: dict[str, object]


def clean_text(text: str) -> str:
    # 保留原始语义，只做换行、空白和不可见字符清洗。
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_text_into_chunks(text: str, *, target_size: int = 800, overlap: int = 120) -> list[TextChunk]:
    # 先按标题和空行保持资料结构，再用固定长度兜底，避免超长 chunk 影响检索。
    cleaned = clean_text(text)
    if not cleaned:
        return []

    sections = _split_sections(cleaned)
    chunks: list[TextChunk] = []
    for title, section_text in sections:
        if _looks_like_qa(section_text) and len(section_text) <= target_size * 2:
            chunks.append(TextChunk(title=title, content=section_text, metadata={"chunk_type": "qa"}))
            continue

        for part in _split_long_text(section_text, target_size=target_size, overlap=overlap):
            chunks.append(
                TextChunk(
                    title=title,
                    content=part,
                    metadata={"chunk_type": "plain_text"},
                )
            )
    return chunks


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    sections: list[tuple[str | None, list[str]]] = []
    current_title: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if re.match(r"^\s{0,3}#{1,6}\s+", line):
            if current_lines:
                sections.append((current_title, current_lines))
                current_lines = []
            current_title = line.lstrip("#").strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def _split_long_text(text: str, *, target_size: int, overlap: int) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 2 <= target_size:
            buffer = f"{buffer}\n\n{paragraph}".strip()
            continue
        if buffer:
            chunks.extend(_force_split(buffer, target_size=target_size, overlap=overlap))
        buffer = paragraph

    if buffer:
        chunks.extend(_force_split(buffer, target_size=target_size, overlap=overlap))
    return chunks


def _force_split(text: str, *, target_size: int, overlap: int) -> list[str]:
    if len(text) <= target_size:
        return [text]

    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + target_size, len(text))
        window = text[start:end]
        split_at = max(window.rfind("。"), window.rfind("？"), window.rfind("；"), window.rfind("\n"))
        if split_at > target_size // 2:
            end = start + split_at + 1
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [part for part in parts if part]


def _looks_like_qa(text: str) -> bool:
    return bool(re.search(r"(^|\n)\s*(Q[:：]|问题[:：])", text)) and bool(
        re.search(r"(^|\n)\s*(A[:：]|答案[:：])", text)
    )

