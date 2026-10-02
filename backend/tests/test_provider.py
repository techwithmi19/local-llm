import pytest

from app.config import settings
from app.services.providers.provider_factory import ProviderFactory


@pytest.mark.skipif(
    not settings.llm_provider,
    reason="LLM_PROVIDER is not configured",
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