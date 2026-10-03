from pathlib import Path

import pytest

from app.services.file_parser import parse_file


@pytest.fixture()
def sample_file(tmp_path: Path) -> Path:
    return tmp_path


def test_parse_text_file(sample_file: Path) -> None:
    path = sample_file / "note.txt"
    path.write_text("Hello from text file.")
    result = parse_file(path, "text/plain")
    assert result == "Hello from text file."


def test_parse_json_file(sample_file: Path) -> None:
    path = sample_file / "data.json"
    path.write_text('{"key": "value"}')
    result = parse_file(path, "application/json")
    assert '"key": "value"' in result


def test_parse_csv_file(sample_file: Path) -> None:
    path = sample_file / "data.csv"
    path.write_text("name,age\nAlice,30")
    result = parse_file(path, "text/csv")
    assert "name,age" in result


def test_parse_image_file(sample_file: Path) -> None:
    path = sample_file / "photo.png"
    path.write_bytes(b"fake-png-data")
    result = parse_file(path, "image/png")
    assert "Image file" in result
    assert "photo.png" in result
