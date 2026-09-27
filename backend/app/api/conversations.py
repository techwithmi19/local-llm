from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.conversation_service import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversations,
    get_messages,
)


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["conversations"],
)


class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"


class ConversationResponse(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: str


class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse    


class ConversationWithMessagesResponse(BaseModel):
    id: int
    title: str
    messages: list[MessageResponse]


@router.post(
    "",
    response_model=ConversationResponse,
)
async def create_conversation_api(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    return await create_conversation(
        db=db,
        title=request.title,
    )


@router.get(
    "",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    db: AsyncSession = Depends(get_db),
):
    return await get_conversations(db)


@router.get(
    "/{conversation_id}",
    response_model=ConversationWithMessagesResponse,
)
async def get_conversation_api(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    conversation = await get_conversation(
        db,
        conversation_id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = await get_messages(
        db,
        conversation_id,
    )

    return ConversationWithMessagesResponse(
        id=conversation.id,
        title=conversation.title,
        messages=[
            MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
            )
            for message in messages
        ],
    )


@router.delete(
    "/{conversation_id}",
)
async def delete_conversation_api(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_conversation(
        db,
        conversation_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {
        "message": "Conversation deleted",
        "conversation_id": conversation_id,
    }