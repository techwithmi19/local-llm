from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

SUPPORTED_LLM_PROVIDERS = {"openai", "kimi", "gemini", "groq"}


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

    @model_validator(mode="after")
    def validate_llm_config(self) -> "Settings":
        provider = self.llm_provider.strip().lower()

        if not provider:
            raise ValueError(
                "LLM_PROVIDER is required. Set it in your .env file "
                "(e.g. LLM_PROVIDER=openai)."
            )

        if provider not in SUPPORTED_LLM_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
            raise ValueError(
                f"Unsupported LLM_PROVIDER: {self.llm_provider!r}. "
                f"Supported providers: {supported}."
            )

        if not self.llm_model.strip():
            raise ValueError(
                "LLM_MODEL is required. Set it in your .env file "
                "(e.g. LLM_MODEL=gpt-4o-mini)."
            )

        return self


settings = Settings()