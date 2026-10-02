from app.services.providers.provider_factory import ProviderFactory

class LLMService:

    def __init__(self) -> None:
        self.provider = ProviderFactory.create()

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        """
        Generate a response using the configured LLM provider.

        Args:
            messages: Conversation history as role/content dicts.
            system_prompt: Optional system instructions.
        """
        return await self.provider.generate(messages, system_prompt)