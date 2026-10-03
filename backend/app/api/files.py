import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.file_service import (
    delete_file,
    get_file,
    get_files,
    parse_file_by_id,
    save_upload,
)

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1",
    tags=["files"],
)


class FileResponse(BaseModel):
    id: int
    conversation_id: int
    original_filename: str
    mime_type: str
    size: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class FileContentResponse(BaseModel):
    content: str | None
    status: str


@router.post(
    "/conversations/{conversation_id}/files",
    response_model=FileResponse,
)
async def upload_file(
    conversation_id: int,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Upload a file and attach it to a conversation."""
    logger.info(
        "Upload request for conversation %s, file: %s (%s bytes)",
        conversation_id,
        file.filename,
        file.size if file.size is not None else "unknown",
    )
    file_record = await save_upload(
        db=db,
        conversation_id=conversation_id,
        upload=file,
    )
    logger.info(
        "Saved file record id=%s filename=%s status=%s",
        file_record.id,
        file_record.original_filename,
        file_record.status,
    )
    return FileResponse.model_validate(file_record)


@router.get(
    "/conversations/{conversation_id}/files",
    response_model=list[FileResponse],
)
async def list_files(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[FileResponse]:
    """List all files attached to a conversation."""
    logger.info("List files request for conversation %s", conversation_id)
    files = await get_files(db, conversation_id)
    logger.info("Returning %s file(s) for conversation %s", len(files), conversation_id)
    return [FileResponse.model_validate(f) for f in files]


@router.delete("/files/{file_id}")
async def delete_file_api(
    file_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a file and remove its stored copy."""
    deleted = await delete_file(db, file_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return {
        "message": "File deleted",
        "file_id": file_id,
    }


@router.get(
    "/files/{file_id}",
    response_model=FileResponse,
)
async def get_file_api(
    file_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Return metadata for a single file."""
    file_record = await get_file(db, file_id)

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return FileResponse.model_validate(file_record)


@router.get(
    "/files/{file_id}/content",
    response_model=FileContentResponse,
)
async def get_file_content(
    file_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileContentResponse:
    """Return extracted text for a parsed file."""
    file_record = await get_file(db, file_id)

    if file_record is None:
        raise HTTPException(
            status_code=404,
            detail="File not found",
        )

    return FileContentResponse(
        content=file_record.extracted_text,
        status=file_record.status,
    )


@router.post(
    "/files/{file_id}/parse",
    response_model=FileResponse,
)
async def reparse_file(
    file_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Re-parse a file on demand."""
    file_record = await parse_file_by_id(db, file_id)
    return FileResponse.model_validate(file_record)
