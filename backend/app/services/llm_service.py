from collections.abc import AsyncIterator
from typing import Any

from app.services.providers.provider_factory import ProviderFactory


class LLMService:

    def __init__(self) -> None:
        self.provider = ProviderFactory.create()

    async def generate(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a complete response using the configured LLM provider.

        Args:
            messages: Conversation history as role/content dicts.
                      Content may be a string or multimodal parts.
            system_prompt: Optional system instructions.

        Returns:
            The assistant's full response text.
        """
        return await self.provider.generate(messages, system_prompt)

    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream response tokens using the configured LLM provider.

        Args:
            messages: Conversation history as role/content dicts.
                      Content may be a string or multimodal parts.
            system_prompt: Optional system instructions.

        Yields:
            Response text tokens from the assistant.
        """
        async for token in self.provider.generate_stream(messages, system_prompt):
            yield token