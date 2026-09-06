from openai import AsyncOpenAI

from app.config import settings
from app.services.providers.base import LLMProvider


class OpenAIProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model

    async def generate(
        self,
        message: str,
        system_prompt: str | None = None,
    ) -> str:

        response = await self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=message,
        )

        return response.output_text