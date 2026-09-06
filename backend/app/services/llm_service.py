from app.services.providers.provider_factory import ProviderFactory

class LLMService:

    def __init__(self) -> None:
        self.provider = ProviderFactory.create()

    async def generate(
        self,
        message: str,
        system_prompt: str | None = None,
    ) -> str:
        return await self.provider.generate(message, system_prompt)