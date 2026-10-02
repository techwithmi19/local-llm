import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_BASE_URL = os.getenv(
    "KIMI_BASE_URL",
    "https://litellm.ai.netcracker.cloud/v1",
)
KIMI_MODEL = os.getenv("KIMI_MODEL", "kimi-k2.6")

if not KIMI_API_KEY:
    raise RuntimeError("KIMI_API_KEY is not configured")

client = AsyncOpenAI(
    api_key=KIMI_API_KEY,
    base_url=KIMI_BASE_URL,
)

app = FastAPI(title="Local LLM Proxy")


class ChatRequest(BaseModel):
    messages: list[dict]
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": KIMI_MODEL,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        response = await client.chat.completions.create(
            model=request.model or KIMI_MODEL,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        return response.model_dump()

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
