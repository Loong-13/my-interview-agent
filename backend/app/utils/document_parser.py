from pathlib import Path

import fitz
from docx import Document


def parse_document_text(path: str, file_type: str | None) -> str:
    file_path = Path(path)
    normalized_type = (file_type or file_path.suffix.removeprefix(".")).lower()

    if normalized_type == "pdf":
        return _parse_pdf(file_path)
    if normalized_type == "docx":
        return _parse_docx(file_path)
    if normalized_type == "txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported file type: {normalized_type}")


def _parse_pdf(path: Path) -> str:
    parts: list[str] = []
    with fitz.open(path) as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts).strip()


def _parse_docx(path: Path) -> str:
    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()

