from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Conversation, Message

async def create_conversation(db: AsyncSession, title: str = "New Conversation") -> Conversation:
    conversation = Conversation(title=title)

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def get_conversations(db: AsyncSession)-> list[Conversation]:
    result = await db.execute(select(Conversation).order_by(Conversation.updated_at.desc()))
    return list(result.scalars().all())


async def get_conversation(db: AsyncSession, conversation_id: int) -> Conversation | None:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


async def delete_conversation(db: AsyncSession, conversation_id: int) -> bool:
    result = await db.execute(delete(Conversation).where(Conversation.id == conversation_id))
    await db.commit()
    return result.rowcount > 0


async def add_message(db: AsyncSession, conversation_id: int, role: str, content: str) -> Message:
    message = Message(conversation_id = conversation_id, role=role, content=content)

    db.add(message)

    # update conversation activity timestamp
    conversation = await get_conversation(db, conversation_id)

    if conversation is not None:
        conversation.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(message)

    return message


async def get_messages(db: AsyncSession, conversation_id: int) -> list[Message]:
    result = await db.execute(select(Message).where(Message.conversation_id == conversation_id)
                              .order_by(Message.created_at.asc(), Message.id.asc()))
    return list(result.scalars().all())