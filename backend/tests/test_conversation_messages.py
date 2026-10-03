from httpx import AsyncClient

from app.api import conversation_messages


class _MockLLMService:
    """Capture the messages passed to the LLM and return a fixed response."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        return "mock response"

    async def generate_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ):
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        for token in ["mock", " ", "response"]:
            yield token


class _FailingStreamLLMService:
    """Simulate a provider whose stream raises after emitting one token."""

    async def generate(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ) -> str:
        return "mock response"

    async def generate_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
    ):
        yield "partial"
        raise RuntimeError("stream failure")


async def test_message_without_file_ids_has_text_content(
    client: AsyncClient,
) -> None:
    """When no file_ids are supplied the user message content is a plain string."""
    mock_service = _MockLLMService()
    conversation_messages.llm_service = mock_service

    response = await client.post("/api/v1/conversations", json={"title": "Test"})
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"message": "Hello"},
    )
    assert response.status_code == 200

    assert len(mock_service.calls) == 1
    history = mock_service.calls[0]["messages"]
    assert history[-1] == {"role": "user", "content": "Hello"}


async def test_message_with_image_file_ids_attaches_image_parts(
    client: AsyncClient,
) -> None:
    """Image file_ids are converted into image_url content parts for the LLM."""
    mock_service = _MockLLMService()
    conversation_messages.llm_service = mock_service

    response = await client.post(
        "/api/v1/conversations",
        json={"title": "Image test"},
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    # Minimal valid 1x1 PNG.
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": ("pixel.png", png_data, "image/png")},
    )
    assert response.status_code == 200
    file_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"message": "Describe this", "file_ids": [file_id]},
    )
    assert response.status_code == 200

    assert len(mock_service.calls) == 1
    history = mock_service.calls[0]["messages"]
    user_message = history[-1]
    assert user_message["role"] == "user"
    assert isinstance(user_message["content"], list)
    assert user_message["content"][0] == {
        "type": "text",
        "text": "Describe this",
    }
    assert user_message["content"][1]["type"] == "image_url"
    assert user_message["content"][1]["image_url"]["url"].startswith(
        "data:image/png;base64,",
    )


async def test_message_with_text_file_id_stays_text_only(
    client: AsyncClient,
) -> None:
    """Non-image file_ids do not produce image_url parts."""
    mock_service = _MockLLMService()
    conversation_messages.llm_service = mock_service

    response = await client.post(
        "/api/v1/conversations",
        json={"title": "Text file test"},
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": ("notes.txt", b"some notes", "text/plain")},
    )
    assert response.status_code == 200
    file_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"message": "Summarize", "file_ids": [file_id]},
    )
    assert response.status_code == 200

    assert len(mock_service.calls) == 1
    history = mock_service.calls[0]["messages"]
    assert history[-1] == {"role": "user", "content": "Summarize"}


async def test_message_ignores_file_ids_from_other_conversations(
    client: AsyncClient,
) -> None:
    """Only file IDs belonging to the target conversation are honored."""
    mock_service = _MockLLMService()
    conversation_messages.llm_service = mock_service

    response = await client.post("/api/v1/conversations", json={"title": "A"})
    assert response.status_code == 200
    conversation_a_id = response.json()["id"]

    response = await client.post("/api/v1/conversations", json={"title": "B"})
    assert response.status_code == 200
    conversation_b_id = response.json()["id"]

    # Upload an image to conversation A.
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    response = await client.post(
        f"/api/v1/conversations/{conversation_a_id}/files",
        files={"file": ("pixel.png", png_data, "image/png")},
    )
    assert response.status_code == 200
    file_a_id = response.json()["id"]

    # Send a message in conversation B referencing A's file.
    response = await client.post(
        f"/api/v1/conversations/{conversation_b_id}/messages",
        json={"message": "Hello", "file_ids": [file_a_id]},
    )
    assert response.status_code == 200

    assert len(mock_service.calls) == 1
    history = mock_service.calls[0]["messages"]
    assert history[-1] == {"role": "user", "content": "Hello"}


async def test_stream_endpoint_yields_user_token_done_events(
    client: AsyncClient,
) -> None:
    """The streaming endpoint emits SSE events and persists assistant text."""
    mock_service = _MockLLMService()
    conversation_messages.llm_service = mock_service

    response = await client.post(
        "/api/v1/conversations",
        json={"title": "Stream test"},
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/stream",
        json={"message": "Hi"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text
    assert '"type": "user_message"' in body
    assert '"type": "token"' in body
    assert '"type": "done"' in body
    assert "mock" in body and "response" in body

    # Verify the assistant message was persisted.
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}",
    )
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "mock response"


async def test_stream_endpoint_yields_error_event_and_persists_user_message(
    client: AsyncClient,
) -> None:
    """A mid-stream failure emits an SSE error event but keeps the user message."""
    conversation_messages.llm_service = _FailingStreamLLMService()

    response = await client.post(
        "/api/v1/conversations",
        json={"title": "Stream error test"},
    )
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/stream",
        json={"message": "Hi"},
    )
    assert response.status_code == 200
    body = response.text
    assert '"type": "error"' in body
    assert "stream failure" in body

    # The user message should still be persisted even though the stream failed.
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}",
    )
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hi"
