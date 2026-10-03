import re
from typing import Any

from google import genai

from app.config import settings
from app.services.providers.base import LLMProvider


class GeminiProvider(LLMProvider):

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )
        self.model = settings.llm_model

    @staticmethod
    def _convert_content(content: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert OpenAI-style content into Gemini parts."""
        if isinstance(content, str):
            return [{"text": content}]

        parts: list[dict[str, Any]] = []
        for part in content:
            part_type = part.get("type")
            if part_type == "text":
                parts.append({"text": part.get("text", "")})
            elif part_type == "image_url":
                image_url = part.get("image_url", {})
                url = image_url.get("url", "") if isinstance(image_url, dict) else ""
                match = re.match(r"^data:([^;]+);base64,(.+)$", url)
                if match:
                    mime_type = match.group(1)
                    data = match.group(2)
                    parts.append({
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": data,
                        },
                    })
            # Unsupported part types are silently ignored.
        return parts

    def _build_contents_and_config(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        # Gemini uses "model" for assistant messages and "user" for user messages.
        contents = [
            {
                "role": "model" if msg["role"] == "assistant" else msg["role"],
                "parts": self._convert_content(msg["content"]),
            }
            for msg in messages
        ]

        config: dict[str, Any] = {}
        if system_prompt:
            config["system_instruction"] = system_prompt

        return contents, config

    async def generate(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> str:
        contents, config = self._build_contents_and_config(
            messages,
            system_prompt,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        return response.text

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ):
        contents, config = self._build_contents_and_config(
            messages,
            system_prompt,
        )

        stream = await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        )

        async for chunk in stream:
            text = chunk.text
            if text:
                yield text