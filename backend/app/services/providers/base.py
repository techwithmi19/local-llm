from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    async def generate(
        self,
        message: str,
        system_prompt: str | None = None,
    ) -> str:
        pass