from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    app_name: str = "Local LLM"
    app_version: str = "0.1.0"
    debug: bool = True

    llm_provider: str = ""
    llm_model: str = ""

    openai_api_key: str = ""
    kimi_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    kimi_base_url: str = ""

    ollama_base_url: str = "http://localhost:11434"

    # CORS: comma-separated list of allowed origins (e.g. "http://localhost:5173,http://localhost:3000")
    cors_origins: str = "*"

    # Database URL. Defaults to a local SQLite file under data/ if left empty.
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()