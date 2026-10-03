from pydantic import BaseModel

from app.api.conversations import MessageResponse

class ChatRequest(BaseModel):
    message: str
    system_prompt: str | None = None
    file_ids: list[int] = []


class ChatResponse(BaseModel):
    response: str


class ConversationWithMessagesResponse(BaseModel):
    id: int
    title: str
    messages: list[MessageResponse]