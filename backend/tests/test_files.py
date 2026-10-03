from pathlib import Path

from httpx import AsyncClient


async def test_upload_and_list_file(client: AsyncClient) -> None:
    """Create a conversation, upload a text file, and list it."""
    # Create a conversation first
    response = await client.post("/api/v1/conversations", json={"title": "File test"})
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    # Upload a file
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": ("hello.txt", b"Hello, world!", "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "hello.txt"
    assert data["mime_type"] == "text/plain"
    assert data["size"] == 13
    assert data["status"] == "parsed"
    file_id = data["id"]

    # Fetch extracted content
    response = await client.get(f"/api/v1/files/{file_id}/content")
    assert response.status_code == 200
    content_data = response.json()
    assert content_data["status"] == "parsed"
    assert content_data["content"] == "Hello, world!"

    # List files
    response = await client.get(f"/api/v1/conversations/{conversation_id}/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 1
    assert files[0]["id"] == file_id

    # Delete file
    response = await client.delete(f"/api/v1/files/{file_id}")
    assert response.status_code == 200

    # List files again
    response = await client.get(f"/api/v1/conversations/{conversation_id}/files")
    assert response.status_code == 200
    assert response.json() == []


async def test_upload_image_file(client: AsyncClient) -> None:
    """Create a conversation, upload a small PNG image, and list it."""
    # Create a conversation first
    response = await client.post("/api/v1/conversations", json={"title": "Image test"})
    assert response.status_code == 200
    conversation_id = response.json()["id"]

    # Minimal valid 1x1 PNG
    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/files",
        files={"file": ("pixel.png", png_data, "image/png")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["original_filename"] == "pixel.png"
    assert data["mime_type"] == "image/png"
    assert data["status"] == "parsed"
    file_id = data["id"]

    # Fetch extracted content (placeholder for images)
    response = await client.get(f"/api/v1/files/{file_id}/content")
    assert response.status_code == 200
    content_data = response.json()
    assert content_data["status"] == "parsed"
    assert "Visual content is not extracted" in content_data["content"]

    # List files
    response = await client.get(f"/api/v1/conversations/{conversation_id}/files")
    assert response.status_code == 200
    files = response.json()
    assert len(files) == 1
    assert files[0]["id"] == file_id



def test_image_to_data_uri(tmp_path: Path) -> None:
    """Verify an image file can be converted to a base64 data URI."""
    import base64

    from app.database.models import File
    from app.services.file_service import image_to_data_uri

    png_data = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    image_path = tmp_path / "pixel.png"
    image_path.write_bytes(png_data)

    file_obj = File(
        conversation_id=1,
        original_filename="pixel.png",
        stored_filename="pixel.png",
        file_path=str(image_path),
        mime_type="image/png",
        size=len(png_data),
        status="parsed",
    )

    data_uri = image_to_data_uri(file_obj)
    assert data_uri is not None
    assert data_uri.startswith("data:image/png;base64,")
    # Verify the payload decodes back to the original PNG bytes.
    encoded = data_uri.split(",")[1]
    assert base64.b64decode(encoded) == png_data
