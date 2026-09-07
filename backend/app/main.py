from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

#API routes
app.include_router(chat_router)

@app.get("/health")
async def health():
    return {"status": "ok",
            "application": settings.app_name,
            "version": settings.app_version
            }

# React frontend
if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST, html=True),
        name="frontend"
    )