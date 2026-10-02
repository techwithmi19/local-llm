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
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:

        # Gemini uses "model" for assistant messages and "user" for user messages.
        contents = [
            {
                "role": "model" if msg["role"] == "assistant" else msg["role"],
                "parts": [{"text": msg["content"]}],
            }
            for msg in messages
        ]

        config = {}
        if system_prompt:
            config["system_instruction"] = system_prompt

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return response.text