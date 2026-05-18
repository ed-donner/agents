"""Shared Pydantic models for the safe-paste orchestration demo."""

from enum import Enum
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ScanResult(BaseModel):
    risk_level: RiskLevel = Field(
        description=(
            "low: no obvious secrets/PII; medium: possible PII (email/phone) or mild leakage; "
            "high: likely tokens/secrets or internal IDs; critical: obvious API keys, bearer tokens, passwords"
        )
    )
    categories: list[str] = Field(
        description="Labels e.g. api_key, bearer_token, email, phone, internal_host, aws_id, none"
    )
    summary: str = Field(description="Short explanation for the user (no secret values).")
    notes_for_orchestrator: str = Field(
        default="",
        description="Internal hint: what the next step should emphasize (still no raw secrets).",
    )


class ExplainerResult(BaseModel):
    summary: str = Field(description="What went wrong in plain language.")
    likely_causes: list[str] = Field(description="Bullet-style causes.")
    next_steps: list[str] = Field(description="Concrete debugging steps.")
    cautions: str = Field(
        default="",
        description="If anything is uncertain, say so here.",
    )


class LeakPrecheckOutput(BaseModel):
    contains_sensitive: bool = Field(
        description="True if the message still appears to contain secrets, tokens, or passwords."
    )
    reason: str = Field(description="Brief reason; do not echo secret substrings.")
