from pydantic import BaseModel

from app.api.conversations import MessageResponse

class ChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None


class ChatResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: str


class ConversationWithMessagesResponse(BaseModel):
    id: int
    title: str
    messages: list[MessageResponse]    