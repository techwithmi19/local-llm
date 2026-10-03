from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.chat import ChatRequest
from app.api.conversations import MessageResponse, SendMessageResponse
from app.services.conversation_service import (
    add_message,
    get_conversation,
    get_messages,
)
from app.services.llm_service import LLMService


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["conversation messages"],
)

llm_service = LLMService()

@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
)
async def send_message(
    conversation_id: int,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> SendMessageResponse:

    conversation = await get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # Build the full conversation history for the LLM
    messages = await get_messages(db, conversation_id)
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    history.append({"role": "user", "content": request.message})

    # Generate assistant response using history
    response = await llm_service.generate(
        messages=history,
        system_prompt=request.system_prompt,
    )

    # Persist the new user message and assistant response
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
        user_message=MessageResponse(
            id=user_message.id,
            conversation_id=user_message.conversation_id,
            role=user_message.role,
            content=user_message.content,
            created_at=user_message.created_at.isoformat(),
        ),
        assistant_message=MessageResponse(
            id=assistant_message.id,
            conversation_id=assistant_message.conversation_id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at.isoformat(),
        ),
    )