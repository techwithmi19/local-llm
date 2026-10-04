import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Provide default LLM config for the test suite so startup validation passes.
# Real provider integration tests still require a matching API key.
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")

from app.database.database import Base, get_db
from app.main import app
from app.services import file_service


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def _create_tables() -> None:
    from app.database import models  # noqa: F401 - register models with metadata

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables() -> None:
    from app.database import models  # noqa: F401 - register models with metadata

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture()
async def client(tmp_path: Path) -> AsyncGenerator[AsyncClient, None]:
    """Yield an HTTP client that uses an in-memory DB and a temp upload dir."""
    await _create_tables()

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    original_upload_dir = file_service.UPLOAD_DIR
    file_service.UPLOAD_DIR = upload_dir

    app.dependency_overrides[get_db] = _get_test_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    file_service.UPLOAD_DIR = original_upload_dir
    await _drop_tables()
