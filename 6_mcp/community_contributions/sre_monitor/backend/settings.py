import os
import ssl
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, field_validator

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_DIR.parents[2]  # .../agents, where the shared .env lives
load_dotenv(REPO_ROOT / ".env", override=True)
load_dotenv(PROJECT_DIR / ".env", override=True)


class LLMConfig(BaseModel):
    provider: Literal["gemini", "openai"] = "gemini"
    gemini_model: str = "gemini-3.5-flash-lite"
    openai_model: str = "gpt-5.4-mini"

    @field_validator("provider", mode="before")
    @classmethod
    def normalise_provider(cls, value: str) -> str:
        value = str(value).strip().lower()
        return {"chatgpt": "openai", "gpt": "openai", "google": "gemini"}.get(value, value)


class MonitorConfig(BaseModel):
    poll_interval_minutes: float = 2
    daily_review_hour: int = 9
    lookback_hours: int = 24
    alert_active_on_first_run: bool = True
    max_postmortem_incidents: int = 15


class VerificationConfig(BaseModel):
    enabled: bool = True
    severities: list[Literal["SEV1", "SEV2", "SEV3", "SEV4"]] = ["SEV1", "SEV2"]
    results_per_query: int = 5


class TracingConfig(BaseModel):
    enabled: bool = True
    project: str = "SRE Monitor"


class EmailConfig(BaseModel):
    recipients: list[str] = []
    priority_recipients: list[str] = []
    dry_run: bool = False


class ServiceConfig(BaseModel):
    name: str
    url: str
    type: Literal["auto", "statuspage", "rss", "zscaler"] = "auto"
    feed_url: str | None = None
    cloud: str | None = None  # zscaler only: the Trust Portal cloud id, for example zsn


class Settings(BaseModel):
    llm: LLMConfig = LLMConfig()
    monitor: MonitorConfig = MonitorConfig()
    verification: VerificationConfig = VerificationConfig()
    tracing: TracingConfig = TracingConfig()
    email: EmailConfig = EmailConfig()
    ca_bundle: str | None = None
    services: list[ServiceConfig]


@lru_cache
def get_settings() -> Settings:
    path = Path(os.getenv("SRE_CONFIG", PROJECT_DIR / "config.yaml"))
    data = yaml.safe_load(path.read_text()) or {}
    if provider := os.getenv("SRE_LLM_PROVIDER"):
        data.setdefault("llm", {})["provider"] = provider
    settings = Settings(**data)
    os.environ["LANGSMITH_TRACING"] = str(settings.tracing.enabled).lower()
    os.environ["LANGSMITH_PROJECT"] = settings.tracing.project
    if settings.ca_bundle and Path(settings.ca_bundle).exists():
        os.environ.setdefault("SSL_CERT_FILE", settings.ca_bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", settings.ca_bundle)
    return settings


def ssl_context() -> ssl.SSLContext:
    get_settings()
    cafile = os.getenv("SSL_CERT_FILE")
    return ssl.create_default_context(cafile=cafile if cafile and Path(cafile).exists() else None)


def model_label() -> str:
    llm = get_settings().llm
    model = llm.gemini_model if llm.provider == "gemini" else llm.openai_model
    return f"{llm.provider}:{model}"


@lru_cache
def get_llm() -> BaseChatModel:
    """The single chat model shared by every agent in a run."""
    llm = get_settings().llm
    if llm.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=llm.openai_model)
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model=llm.gemini_model, temperature=0)
