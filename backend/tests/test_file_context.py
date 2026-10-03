from app.database.models import File
from app.services.file_service import build_file_context


def test_build_file_context() -> None:
    files = [
        File(
            id=1,
            conversation_id=1,
            original_filename="notes.txt",
            stored_filename="abc.txt",
            file_path="/tmp/abc.txt",
            mime_type="text/plain",
            size=12,
            status="parsed",
            extracted_text="Important note.",
        ),
    ]

    context = build_file_context(files)

    assert "Use the following uploaded files as context" in context
    assert "--- Start of notes.txt ---" in context
    assert "Important note." in context
    assert "--- End of notes.txt ---" in context


def test_build_file_context_empty() -> None:
    assert build_file_context([]) == ""
