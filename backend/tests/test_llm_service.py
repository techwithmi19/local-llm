from collections.abc import AsyncIterator

import pytest

from app.services.llm_service import LLMService
from app.services.providers.base import LLMProvider


class _FakeProvider(LLMProvider):
    def __init__(self, stream_tokens: list[str], generate_text: str) -> None:
        self.stream_tokens = stream_tokens
        self.generate_text = generate_text
        self.generate_called = False

    async def generate(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> str:
        self.generate_called = True
        return self.generate_text

    async def generate_stream(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        for token in self.stream_tokens:
            yield token


async def test_generate_stream_yields_provider_tokens_without_fallback():
    fake = _FakeProvider(stream_tokens=["Hello", " world"], generate_text="fallback")
    service = LLMService()
    service.provider = fake

    tokens = [token async for token in service.generate_stream([])]

    assert tokens == ["Hello", " world"]
    assert fake.generate_called is False


async def test_generate_stream_falls_back_when_stream_is_empty():
    fake = _FakeProvider(stream_tokens=[], generate_text="full response")
    service = LLMService()
    service.provider = fake

    tokens = [token async for token in service.generate_stream([])]

    assert tokens == ["full response"]
    assert fake.generate_called is True


async def test_generate_stream_does_not_yield_when_generate_returns_empty():
    fake = _FakeProvider(stream_tokens=[], generate_text="")
    service = LLMService()
    service.provider = fake

    tokens = [token async for token in service.generate_stream([])]

    assert tokens == []
    assert fake.generate_called is True
