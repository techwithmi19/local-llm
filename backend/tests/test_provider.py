import pytest

from app.config import settings
from app.services.providers.provider_factory import ProviderFactory


def _provider_api_key_configured() -> bool:
    provider = settings.llm_provider.lower()
    api_key = getattr(settings, f"{provider}_api_key", "")
    return bool(api_key)


@pytest.mark.skipif(
    not _provider_api_key_configured(),
    reason="API key for the configured LLM_PROVIDER is not set",
)
async def test_provider_generates_response():
    """Integration test: verify the configured provider returns a response."""
    provider = ProviderFactory.create()

    messages = [
        {"role": "user", "content": "Say hello in one sentence."}
    ]

    response = await provider.generate(messages=messages)

    assert isinstance(response, str)
    assert len(response) > 0