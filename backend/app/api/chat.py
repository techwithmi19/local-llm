from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)

llm_service = LLMService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    response = await llm_service.generate(
        message=request.message,
        system_prompt=request.system_prompt,
    )
    return ChatResponse(response=response)