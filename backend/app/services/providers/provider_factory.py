from app.config import settings
from app.services.providers.base import LLMProvider

class ProviderFactory:

    @staticmethod
    def create() -> LLMProvider:
        provider = settings.llm_provider.lower()

        if provider == "openai":
            from app.services.providers.openai_provider import OpenAIProvider
            return OpenAIProvider()
        
        if provider == "gemini":
            from app.services.providers.gemini_provider import GeminiProvider
            return GeminiProvider()
        
        if provider == "groq":
            from app.services.providers.groq_provider import GroqProvider
            return GroqProvider()

        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")