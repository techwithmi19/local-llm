from __future__ import annotations

import base64
import logging
import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, File
from app.services.file_parser import parse_file

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = BASE_DIR / "data" / "uploads"

# 10 MB default cap
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed MIME type prefixes and exact matches for Phase 1 uploads.
# Phase 2 will add content parsing for each of these.
ALLOWED_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
    "application/json",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/zip",
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}

ALLOWED_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".xls",
    ".zip",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
}


def _ensure_upload_dir() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _guess_mime_type(filename: str, content_type: str | None) -> str:
    if content_type:
        return content_type
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def _validate_file(file: UploadFile, content: bytes) -> None:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    mime_type = _guess_mime_type(filename, file.content_type)
    logger.info("_validate_file: filename=%s mime=%s ext=%s size=%s", filename, mime_type, extension, len(content))

    if len(content) > MAX_FILE_SIZE:
        logger.warning("_validate_file: file too large %s bytes", len(content))
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE / (1024 * 1024):.0f} MB",
        )

    if mime_type not in ALLOWED_MIME_TYPES and extension not in ALLOWED_EXTENSIONS:
        logger.warning("_validate_file: unsupported type mime=%s ext=%s", mime_type, extension)
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {mime_type}",
        )


async def save_upload(
    db: AsyncSession,
    conversation_id: int,
    upload: UploadFile,
) -> File:
    """Persist an uploaded file to disk and record it in the database."""
    logger.info("save_upload called: conversation=%s file=%s", conversation_id, upload.filename)
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None:
        logger.warning("save_upload: conversation %s not found", conversation_id)
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    content = await upload.read()
    logger.info("save_upload: read %s bytes for %s", len(content), upload.filename)
    _validate_file(upload, content)

    _ensure_upload_dir()

    original_filename = Path(upload.filename or "unnamed").name
    extension = Path(original_filename).suffix
    stored_filename = f"{uuid4().hex}{extension}"

    conversation_dir = UPLOAD_DIR / str(conversation_id)
    conversation_dir.mkdir(parents=True, exist_ok=True)

    file_path = conversation_dir / stored_filename
    with file_path.open("wb") as buffer:
        buffer.write(content)

    file_record = File(
        conversation_id=conversation_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        mime_type=_guess_mime_type(original_filename, upload.content_type),
        size=len(content),
        status="pending",
    )

    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)

    # Attempt to extract text immediately after upload.
    await _extract_text(db, file_record)

    return file_record


async def _extract_text(db: AsyncSession, file_record: File) -> None:
    """Parse the stored file and update the record with extracted text."""
    logger.info("_extract_text: parsing %s", file_record.original_filename)
    try:
        extracted = parse_file(
            Path(file_record.file_path),
            file_record.mime_type,
        )
        file_record.extracted_text = extracted
        file_record.status = "parsed"
        logger.info("_extract_text: parsed %s successfully", file_record.original_filename)
    except Exception as exc:
        logger.exception("_extract_text: failed to parse %s", file_record.original_filename)
        file_record.status = "failed"

    db.add(file_record)
    await db.commit()
    await db.refresh(file_record)


async def parse_file_by_id(db: AsyncSession, file_id: int) -> File:
    """Re-parse a file on demand."""
    file_record = await db.get(File, file_id)
    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    await _extract_text(db, file_record)
    return file_record


async def get_files(db: AsyncSession, conversation_id: int) -> list[File]:
    """Return all files attached to a conversation, oldest first."""
    result = await db.execute(
        select(File)
        .where(File.conversation_id == conversation_id)
        .order_by(File.created_at.asc())
    )
    return list(result.scalars().all())


async def get_parsed_files(db: AsyncSession, conversation_id: int) -> list[File]:
    """Return files with successfully extracted text for a conversation."""
    result = await db.execute(
        select(File)
        .where(
            File.conversation_id == conversation_id,
            File.status == "parsed",
            File.extracted_text.isnot(None),
        )
        .order_by(File.created_at.asc())
    )
    return list(result.scalars().all())


def build_file_context(files: list[File]) -> str:
    """Build a single context string from parsed file contents."""
    if not files:
        return ""

    parts = [
        "Use the following uploaded files as context when answering:",
        "",
    ]
    for file in files:
        parts.append(f"--- Start of {file.original_filename} ---")
        parts.append(file.extracted_text or "")
        parts.append(f"--- End of {file.original_filename} ---")
        parts.append("")

    return "\n".join(parts)


def _is_image(file_record: File) -> bool:
    """Return True if the file is an image."""
    return file_record.mime_type.startswith("image/") or Path(
        file_record.original_filename,
    ).suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def image_to_data_uri(file_record: File) -> str | None:
    """Read an image file and return it as a base64 data URI."""
    if not _is_image(file_record):
        return None

    path = Path(file_record.file_path)
    if not path.exists():
        logger.warning("image_to_data_uri: file not found %s", file_record.file_path)
        return None

    mime = file_record.mime_type or "image/png"
    if mime == "application/octet-stream":
        # Fall back to extension-based detection.
        ext = Path(file_record.original_filename).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        mime = mime_map.get(ext, "image/png")

    try:
        data = path.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        logger.exception("image_to_data_uri: failed to read %s", file_record.file_path)
        return None


async def get_file(db: AsyncSession, file_id: int) -> File | None:
    """Return a single file record by ID."""
    return await db.get(File, file_id)


async def delete_file(db: AsyncSession, file_id: int) -> bool:
    """Delete a file record and its stored copy."""
    file_record = await db.get(File, file_id)
    if file_record is None:
        return False

    try:
        Path(file_record.file_path).unlink(missing_ok=True)
        # Remove the conversation folder if it becomes empty.
        conversation_dir = UPLOAD_DIR / str(file_record.conversation_id)
        if conversation_dir.exists() and not any(conversation_dir.iterdir()):
            shutil.rmtree(conversation_dir)
    except OSError:
        # Continue even if the filesystem cleanup fails; the DB record must go.
        pass

    await db.delete(file_record)
    await db.commit()
    return True
