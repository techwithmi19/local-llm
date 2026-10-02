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
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:

        request_messages = list(messages)

        if system_prompt:
            request_messages.insert(
                0,
                {
                    "role": "system",
                    "content": system_prompt,
                },
            )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=request_messages,
        )

        return response.choices[0].message.content or ""