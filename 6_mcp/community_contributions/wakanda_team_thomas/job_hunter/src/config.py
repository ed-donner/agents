"""Configuration management for Job Hunter system."""

import os
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
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
        default=0.90, ge=0.0, le=1.0, description="Minimum match score (0.0-1.0)"
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
    return Settings()


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
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"


def ensure_directories() -> None:
    """Ensure required directories exist."""
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
