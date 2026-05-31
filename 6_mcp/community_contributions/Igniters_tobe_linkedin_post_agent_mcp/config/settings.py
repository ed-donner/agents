from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PROJECT_ROOT.parents[2]
load_dotenv(REPO_ROOT / ".env", override=False)
load_dotenv(PROJECT_ROOT / ".env", override=True)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    data_dir: Path
    db_path: Path
    keyring_service_name: str
    openrouter_api_key: str | None
    openrouter_model: str
    openrouter_base_url: str
    openrouter_http_referer: str | None
    openrouter_title: str | None
    linkedin_client_id: str | None
    linkedin_client_secret: str | None
    linkedin_redirect_uri: str | None

    def validate_openrouter(self) -> None:
        missing = []
        if not self.openrouter_api_key:
            missing.append("OPENROUTER_API_KEY")
        if not self.openrouter_model:
            missing.append("OPENROUTER_MODEL")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    def validate_linkedin(self) -> None:
        missing = []
        if not self.linkedin_client_id:
            missing.append("LINKEDIN_CLIENT_ID")
        if not self.linkedin_client_secret:
            missing.append("LINKEDIN_CLIENT_SECRET")
        if not self.linkedin_redirect_uri:
            missing.append("LINKEDIN_REDIRECT_URI")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        parsed = urlparse(self.linkedin_redirect_uri)
        if not parsed.scheme or not parsed.hostname or not parsed.path:
            raise RuntimeError("LINKEDIN_REDIRECT_URI must be a valid absolute URL")

    def validate_all(self) -> None:
        self.validate_openrouter()
        self.validate_linkedin()
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def callback_host(self) -> str:
        self.validate_linkedin()
        parsed = urlparse(self.linkedin_redirect_uri or "")
        return parsed.hostname or "127.0.0.1"

    @property
    def callback_port(self) -> int:
        self.validate_linkedin()
        parsed = urlparse(self.linkedin_redirect_uri or "")
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == "https" else 80

    @property
    def callback_path(self) -> str:
        self.validate_linkedin()
        parsed = urlparse(self.linkedin_redirect_uri or "")
        return parsed.path or "/"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = PROJECT_ROOT
    data_dir = project_root / "data"
    db_path = data_dir / "linkedin_post_agent.db"
    return Settings(
        project_root=project_root,
        data_dir=data_dir,
        db_path=db_path,
        keyring_service_name="linkedin_post_agent_mcp",
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        openrouter_base_url=os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1"),
        openrouter_http_referer=os.getenv("OPENROUTER_HTTP_REFERER"),
        openrouter_title=os.getenv("OPENROUTER_TITLE"),
        linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID"),
        linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET"),
        linkedin_redirect_uri=os.getenv("LINKEDIN_REDIRECT_URI"),
    )
