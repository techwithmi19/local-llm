from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from pypdf import PdfReader


MAX_EXTRACTED_CHARS = 50_000


def _truncate(text: str) -> str:
    if len(text) <= MAX_EXTRACTED_CHARS:
        return text
    return text[:MAX_EXTRACTED_CHARS] + "\n\n[Content truncated due to length.]"


def parse_file(file_path: Path, mime_type: str) -> str:
    """Extract plain text from a supported document.

    Supports:
      - text/plain, text/markdown, text/csv, application/json
      - application/pdf
      - application/vnd.openxmlformats-officedocument.wordprocessingml.document
      - image/* (returns a placeholder; visual content is not OCR'd)
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = path.suffix.lower()

    if mime_type.startswith("text/") or extension in {".txt", ".md", ".csv"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        return _truncate(text)

    if mime_type == "application/json" or extension == ".json":
        raw = path.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(raw)
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pretty = raw
        return _truncate(pretty)

    if mime_type == "application/pdf" or extension == ".pdf":
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                parts.append(page_text)
        return _truncate("\n\n".join(parts))

    if (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or extension == ".docx"
    ):
        document = Document(str(path))
        parts = [paragraph.text for paragraph in document.paragraphs]
        return _truncate("\n".join(parts))

    if mime_type.startswith("image/") or extension in {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".bmp",
    }:
        return (
            f"[Image file: {path.name}. "
            "Visual content is not extracted in this version.]"
        )

    raise ValueError(f"No parser available for mime type: {mime_type}")
