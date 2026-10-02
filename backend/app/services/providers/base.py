from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            messages: Conversation history as a list of role/content dicts.
                      Roles are "user" and "assistant".
            system_prompt: Optional system instructions.

        Returns:
            The assistant's response text.
        """
        pass