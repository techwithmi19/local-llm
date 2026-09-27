from openai import AsyncOpenAI

from app.config import settings
from app.services.providers.base import LLMProvider


class KimiProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.kimi_api_key,
            base_url=settings.kimi_base_url,
        )
        self.model = settings.llm_model

    async def generate(
        self,
        message: str,
        system_prompt: str | None = None,
    ) -> str:

        messages = []

        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })

        messages.append({
            "role": "user",
            "content": message,
        })

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return response.choices[0].message.content or ""