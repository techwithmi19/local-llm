import truststore

truststore.inject_into_ssl()

from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.conversations import router as conversation_router
from app.api.conversation_messages import router as conversation_messages_router
from app.config import settings
from app.database.database import init_db


BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
_cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes
app.include_router(chat_router)
app.include_router(conversation_router)
app.include_router(conversation_messages_router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/v1/config")
async def get_config():
    """Expose non-sensitive configuration to the frontend."""
    return {
        "app_name": settings.app_name,
        "provider": settings.llm_provider,
        "model": settings.llm_model,
    }


# React frontend
if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST, html=True),
        name="frontend",
    )