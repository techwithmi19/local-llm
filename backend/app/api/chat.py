from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"],
)

llm_service = LLMService()

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    messages = [
        {"role": "user", "content": request.message},
    ]
    response = await llm_service.generate(
        messages=messages,
        system_prompt=request.system_prompt,
    )

    return ChatResponse(response=response)