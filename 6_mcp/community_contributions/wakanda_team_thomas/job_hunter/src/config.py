"""Configuration management for Job Hunter system."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).parent.parent


def _resolve_env_file() -> Path:
    """Resolve .env from project root or nearest parent directory."""
    for base in [PROJECT_ROOT, *PROJECT_ROOT.parents]:
        candidate = base / ".env"
        if candidate.exists():
            return candidate
    return PROJECT_ROOT / ".env"


ENV_FILE = _resolve_env_file()
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")

    # Langfuse Observability
    langfuse_public_key: str = Field(default="", description="Langfuse public key")
    langfuse_secret_key: str = Field(default="", description="Langfuse secret key")
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", description="Langfuse host URL"
    )

    # Database
    database_url: str = Field(
        default="sqlite:///./job_hunter.db", description="SQLite database URL"
    )

    # Job Search Settings
    job_match_threshold: float = Field(
        default=0.60, ge=0.0, le=1.0, description="Minimum match score (0.0-1.0)"
    )
    search_interval_hours: int = Field(
        default=24, ge=1, description="Hours between scheduled searches"
    )

    # Application
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    @property
    def langfuse_enabled(self) -> bool:
        """Check if Langfuse is configured."""
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def database_path(self) -> Path:
        """Extract database file path from URL."""
        url = self.database_url
        if url.startswith("sqlite:///"):
            return Path(url.replace("sqlite:///", ""))
        return Path("job_hunter.db")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    # OpenAI SDK clients look for OPENAI_API_KEY in os.environ by default.
    if settings.openai_api_key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    return settings


# Job status constants
class JobStatus:
    """Job application status constants."""

    NEW = "new"
    REVIEWING = "reviewing"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

    ALL = [NEW, REVIEWING, APPLIED, INTERVIEW, REJECTED, ACCEPTED]


# Job board source constants
class JobSource:
    """Job board source identifiers."""

    REMOTEOK = "remoteok"
    REMOTIVE = "remotive"
    ARBEITNOW = "arbeitnow"

    ALL = [REMOTEOK, REMOTIVE, ARBEITNOW]


# Matching weight configuration
class MatchWeights:
    """Weights for job-profile matching components."""

    SKILLS = 0.40
    EXPERIENCE = 0.25
    KEYWORDS = 0.20
    REQUIREMENTS = 0.15


# Project paths
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


def ensure_directories() -> None:
    """Ensure required directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
