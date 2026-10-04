import logging
from collections.abc import AsyncIterator
from typing import Any

from app.services.providers.base import LLMProvider
from app.services.providers.provider_factory import ProviderFactory


logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self._provider: LLMProvider | None = None

    @property
    def provider(self) -> LLMProvider:
        if self._provider is None:
            self._provider = ProviderFactory.create()
        return self._provider

    @provider.setter
    def provider(self, value: LLMProvider) -> None:
        self._provider = value

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

        If the provider's stream yields no tokens (e.g., because a proxy or
        upstream model does not support streaming), fall back to the
        non-streaming generate() so the user still receives a response.

        Args:
            messages: Conversation history as role/content dicts.
                      Content may be a string or multimodal parts.
            system_prompt: Optional system instructions.

        Yields:
            Response text tokens from the assistant.
        """
        yielded = False
        async for token in self.provider.generate_stream(messages, system_prompt):
            yielded = True
            yield token

        if not yielded:
            logger.warning(
                "Provider stream yielded no tokens; "
                "falling back to non-streaming generate().",
            )
            text = await self.provider.generate(messages, system_prompt)
            if text:
                yield text