from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a complete response from the LLM.

        Args:
            messages: Conversation history as a list of role/content dicts.
                      Roles are "user" and "assistant". Content may be a
                      string or a multimodal list of content parts.
            system_prompt: Optional system instructions.

        Returns:
            The assistant's full response text.
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream response tokens from the LLM as they are generated.

        Args:
            messages: Conversation history as a list of role/content dicts.
                      Roles are "user" and "assistant". Content may be a
                      string or a multimodal list of content parts.
            system_prompt: Optional system instructions.

        Yields:
            Response text tokens from the assistant.
        """
        yield ""
