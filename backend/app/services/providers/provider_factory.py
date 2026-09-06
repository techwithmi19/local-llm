from app.config import settings
from app.services.providers.base import LLMProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.groq_provider import GroqProvider

class ProviderFactory:

    @staticmethod
    def create() -> LLMProvider:
        provider = settings.llm_provider.lower()

        if provider == "openai":
            return OpenAIProvider()
        if provider == "gemini":
            return GeminiProvider()
        if provider == "groq":
            return GroqProvider()

        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")