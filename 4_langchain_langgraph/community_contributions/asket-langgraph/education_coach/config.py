from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _agents_repo_root() -> Path:
    return _project_root().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_top_p: float | None = None
    openai_max_tokens: int | None = None
    openai_worker_streaming: bool = True
    wikipedia_lang: str = "en"

    openai_embedding_model: str = "text-embedding-3-small"
    course_materials_path: str | None = None
    rag_enabled: bool = True
    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 200
    rag_top_k: int = 4

    sendgrid_api_key: str | None = None
    sendgrid_from_email: str | None = None

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


def bootstrap_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    repo_env = _agents_repo_root() / ".env"
    local_env = _project_root() / ".env"
    if repo_env.is_file():
        load_dotenv(repo_env, override=False)
    if local_env.is_file():
        load_dotenv(local_env, override=True)
    get_settings.cache_clear()
