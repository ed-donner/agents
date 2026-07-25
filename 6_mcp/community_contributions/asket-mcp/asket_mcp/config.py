from functools import lru_cache
from pathlib import Path
from typing import Literal, cast

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Transport = Literal["stdio", "sse", "streamable-http"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(
        default=Path("data"),
        validation_alias=AliasChoices("ASKET_MCP_DATA_DIR", "data_dir"),
    )
    brain_root: Path = Field(
        default=Path("PersonalStudyBrain"),
        validation_alias=AliasChoices("PERSONAL_STUDY_BRAIN_DIR", "ASKET_BRAIN_ROOT", "brain_root"),
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("ASKET_MCP_LOG_LEVEL", "log_level"),
    )

    mcp_transport: str = Field(
        default="stdio",
        validation_alias=AliasChoices("ASKET_MCP_TRANSPORT", "mcp_transport"),
    )
    mcp_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("ASKET_MCP_HOST", "mcp_host"),
    )
    mcp_port: int = Field(
        default=8765,
        validation_alias=AliasChoices("ASKET_MCP_PORT", "mcp_port"),
    )

    pushover_user: str | None = None
    pushover_token: str | None = None

    httpx_timeout_seconds: float = Field(
        default=30.0,
        validation_alias=AliasChoices("ASKET_MCP_HTTP_TIMEOUT", "httpx_timeout_seconds"),
    )
    fetch_max_bytes: int = Field(
        default=500_000,
        ge=1024,
        validation_alias=AliasChoices("ASKET_MCP_FETCH_MAX_BYTES", "fetch_max_bytes"),
    )
    fetch_user_agent: str = Field(
        default="AsketMCP/3.0 (+https://github.com/modelcontextprotocol)",
        validation_alias=AliasChoices("ASKET_MCP_FETCH_USER_AGENT", "fetch_user_agent"),
    )

    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
    )
    chroma_persist_path: Path | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_CHROMA_PATH", "CHROMA_DB_PATH", "CHROMA_PATH"),
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("ASKET_EMBEDDING_MODEL", "EMBEDDING_MODEL"),
    )
    chat_model: str = Field(
        default="gpt-4o-mini",
        validation_alias=AliasChoices("ASKET_CHAT_MODEL", "OPENAI_CHAT_MODEL"),
    )
    rag_top_k: int = Field(
        default=8,
        ge=1,
        le=48,
        validation_alias=AliasChoices("ASKET_RAG_TOP_K"),
    )
    semantic_chunk_chars: int = Field(
        default=1600,
        ge=200,
        le=32000,
        validation_alias=AliasChoices("ASKET_SEMANTIC_CHUNK_CHARS"),
    )
    semantic_chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=8000,
        validation_alias=AliasChoices("ASKET_SEMANTIC_CHUNK_OVERLAP"),
    )

    ui_auth_username: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_AUTH_USERNAME"),
    )
    ui_auth_password: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_AUTH_PASSWORD"),
    )
    ui_root_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_ROOT_PATH", "GRADIO_ROOT_PATH"),
    )
    ui_ssl_certfile: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_SSL_CERTFILE"),
    )
    ui_ssl_keyfile: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_SSL_KEYFILE"),
    )

    @field_validator("ui_ssl_certfile", "ui_ssl_keyfile", mode="before")
    @classmethod
    def _empty_ui_ssl_path_is_none(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s or None
        return str(v).strip() or None

    ui_ssl_verify: bool = Field(
        default=True,
        validation_alias=AliasChoices("ASKET_UI_SSL_VERIFY"),
    )
    ui_gradio_analytics: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_GRADIO_ANALYTICS"),
    )
    ui_ssr_mode: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_SSR_MODE", "GRADIO_SSR_MODE"),
    )
    ui_max_threads: int = Field(
        default=16,
        ge=1,
        le=256,
        validation_alias=AliasChoices("ASKET_UI_MAX_THREADS"),
    )
    ui_strict_cors: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_STRICT_CORS"),
    )
    ui_share: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_SHARE"),
    )
    ui_debug: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_DEBUG", "GRADIO_DEBUG"),
    )
    ui_quiet: bool = Field(
        default=True,
        validation_alias=AliasChoices("ASKET_UI_QUIET"),
    )
    ui_minimal_footer: bool = Field(
        default=False,
        validation_alias=AliasChoices("ASKET_UI_MINIMAL_FOOTER"),
    )
    ui_auth_message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ASKET_UI_AUTH_MESSAGE"),
    )

    def gradio_auth(self) -> list[tuple[str, str]] | None:
        u, p = self.ui_auth_username, self.ui_auth_password
        if u and p:
            return [(u.strip(), p)]
        return None

    def chroma_dir(self) -> Path:
        if self.chroma_persist_path is not None:
            p = Path(self.chroma_persist_path).expanduser()
            return p.resolve() if p.is_absolute() else (Path.cwd() / p).resolve()
        d = Path(self.data_dir).expanduser()
        if not d.is_absolute():
            d = Path.cwd() / d
        return (d.resolve() / "chroma")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def mcp_log_level() -> LogLevel:
    raw = (get_settings().log_level or "INFO").upper()
    allowed: set[str] = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if raw in allowed:
        return cast(LogLevel, raw)
    return "INFO"


def normalized_transport() -> Transport:
    t = (get_settings().mcp_transport or "stdio").strip().lower()
    if t in ("http", "streamable", "streamable-http", "streamable_http"):
        return "streamable-http"
    if t in ("sse", "server-sent-events"):
        return "sse"
    return "stdio"
