import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.conversations import MessageResponse, SendMessageResponse

logger = logging.getLogger(__name__)
from app.database.database import get_db
from app.models.chat import ChatRequest
from app.services.conversation_service import (
    add_message,
    get_conversation,
    get_messages,
)
from app.services.file_service import (
    build_file_context,
    get_files,
    get_parsed_files,
    image_to_data_uri,
)
from app.services.llm_service import LLMService


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["conversation messages"],
)

llm_service = LLMService()


def _sse_event(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _build_history(
    db: AsyncSession,
    conversation_id: int,
    request: ChatRequest,
) -> tuple[list[dict[str, Any]], str | None]:
    """Build the LLM history and system prompt for a message request."""
    parsed_files = await get_parsed_files(db, conversation_id)
    file_context = build_file_context(parsed_files)

    system_prompt = request.system_prompt
    if file_context:
        if system_prompt:
            system_prompt = f"{system_prompt}\n\n{file_context}"
        else:
            system_prompt = file_context

    messages = await get_messages(db, conversation_id)
    history: list[dict[str, Any]] = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # Attach any image files selected for this turn as multimodal content parts
    # on the current user message. Only files whose IDs are supplied by the
    # client are included, which avoids resending every image in the
    # conversation on each turn.
    all_files = await get_files(db, conversation_id)
    selected_file_ids = set(request.file_ids)
    image_uris = [
        uri
        for file in all_files
        if file.id in selected_file_ids
        and (uri := image_to_data_uri(file)) is not None
    ]

    if image_uris:
        content_parts: list[dict[str, Any]] = [
            {"type": "text", "text": request.message or "Describe this image."},
        ]
        for uri in image_uris:
            content_parts.append(
                {"type": "image_url", "image_url": {"url": uri}},
            )
        history.append({"role": "user", "content": content_parts})
    else:
        history.append({"role": "user", "content": request.message})

    return history, system_prompt


async def _validate_conversation(
    db: AsyncSession,
    conversation_id: int,
) -> None:
    conversation = await get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )


def _message_response(message: Any) -> MessageResponse:
    return MessageResponse(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at.isoformat(),
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
)
async def send_message(
    conversation_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:
    await _validate_conversation(db, conversation_id)
    history, system_prompt = await _build_history(
        db,
        conversation_id,
        request,
    )

    response = await llm_service.generate(
        messages=history,
        system_prompt=system_prompt,
    )

    user_message = await add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )
    assistant_message = await add_message(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=response,
    )

    return SendMessageResponse(
        user_message=_message_response(user_message),
        assistant_message=_message_response(assistant_message),
    )


@router.post("/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    await _validate_conversation(db, conversation_id)
    history, system_prompt = await _build_history(
        db,
        conversation_id,
        request,
    )

    # Persist the user message up front so the conversation history remains
    # consistent even if the stream is interrupted.
    user_message = await add_message(
        db=db,
        conversation_id=conversation_id,
        role="user",
        content=request.message,
    )

    async def event_generator():
        try:
            yield _sse_event(
                {
                    "type": "user_message",
                    "user_message": _message_response(
                        user_message,
                    ).model_dump(mode="json"),
                },
            )

            assistant_content = ""
            async for token in llm_service.generate_stream(
                messages=history,
                system_prompt=system_prompt,
            ):
                assistant_content += token
                yield _sse_event({"type": "token", "token": token})

            assistant_message = await add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
            )
            yield _sse_event(
                {
                    "type": "done",
                    "assistant_message": _message_response(
                        assistant_message,
                    ).model_dump(mode="json"),
                },
            )
        except Exception as exc:
            logger.exception("Streaming response failed")
            yield _sse_event(
                {
                    "type": "error",
                    "error": str(exc),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )