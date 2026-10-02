import pytest
from groq import AsyncGroq

from app.config import settings


@pytest.mark.skipif(
    not settings.groq_api_key,
    reason="GROQ_API_KEY is not configured",
)
async def test_groq_models_list():
    """Integration test: verify Groq returns a non-empty model list."""
    client = AsyncGroq(api_key=settings.groq_api_key)
    models = await client.models.list()

    assert len(models.data) > 0