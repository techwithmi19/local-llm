from google import genai

from app.config import settings
from app.services.providers.base import LLMProvider


class GeminiProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )
        self.model = settings.llm_model

    async def generate(
        self,
        message: str,
        system_prompt: str | None = None,
    ) -> str:

        prompt = message

        if system_prompt:
            prompt = (
                f"System instructions:\n{system_prompt}\n\n"
                f"User:\n{message}"
            )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        return response.text