from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


SUPPORTED_LANGUAGES = (
    "en",
    "es",
    "zh",
    "hi",
    "ko",
    "vi",
    "tl",
    "fa",
    "ar",
    "pt",
    "pa",
    "ur",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://civicvoice:civicvoice@localhost:5432/civicvoice"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "change-me-local-dev-only"
    backend_host: str = "0.0.0.0"
    backend_port: int = 5001

    # Cookie settings — secure=False for local http
    session_cookie_name: str = "civicvoice_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 14  # 14 days
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    login_max_failures: int = 10
    login_lockout_seconds: int = 600  # 10 minutes

    # Ask
    ask_rate_limit: int = 20
    ask_rate_window_seconds: int = 60
    ask_cache_ttl_seconds: int = 60 * 30  # 30 minutes

    # LLM (empty key => document-only fallback, never invent summaries)
    civicvoice_llm_api_key: str = ""
    civicvoice_llm_base_url: str = ""
    civicvoice_llm_model: str = ""

    # Embeddings (sentence-transformers e5). Off until model is installed.
    embeddings_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
