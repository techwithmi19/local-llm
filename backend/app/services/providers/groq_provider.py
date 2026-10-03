from typing import Any

from groq import AsyncGroq

from app.config import settings
from app.services.providers.base import LLMProvider


class GroqProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = AsyncGroq(
            api_key=settings.groq_api_key,
            default_headers={
                "Groq-Model-Version": "latest"
            },
        )
        self.model = settings.llm_model

    def _build_request_messages(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> list[dict[str, Any]]:
        request_messages = list(messages)

        if system_prompt:
            request_messages.insert(
                0,
                {
                    "role": "system",
                    "content": system_prompt,
                },
            )

        return request_messages

    async def generate(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> str:
        request_messages = self._build_request_messages(
            messages,
            system_prompt,
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=request_messages,
        )

        return response.choices[0].message.content or ""

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ):
        request_messages = self._build_request_messages(
            messages,
            system_prompt,
        )

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=request_messages,
            stream=True,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield content