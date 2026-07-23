"""
user_config.py — Single source of truth for all user-specific configuration.

Loads config.yaml (candidate contact info, profile/criteria paths, search
parameters) so that every pipeline stage (job_search, job_prefilter,
job_evaluator, cover_letter, job_ui) reads from one place instead of
hardcoding a specific person's details.

To adapt this project to yourself: copy config.example.yaml -> config.yaml
and fill in your own name, contact details, and search preferences. Then
replace profile.md and criteria.md with your own resume/criteria in the
same Markdown structure.

Usage:
    from user_config import get_config
    cfg = get_config()
    cfg.candidate.name
    cfg.search.terms
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY, FIRECRAWL_API_KEY, etc.) from .env
# at the project root. This runs once, as soon as any pipeline module imports
# user_config (which all of them do), so every stage — job_search, job_prefilter,
# job_evaluator, cover_letter, job_ui, app.py — gets the keys automatically
# without each script needing its own load_dotenv() call.
load_dotenv()

CONFIG_PATH = Path("config.yaml")


@dataclass
class CandidateConfig:
    name: str
    email: str
    phone: str
    location: str


@dataclass
class SearchConfig:
    terms: list[str]
    location: str
    results_per_call: int = 25
    hours_old: int = 240


@dataclass
class PrefilterConfig:
    shortlist_min_size: int = 30


@dataclass
class EvaluatorConfig:
    top_n: int = 10


@dataclass
class AppConfig:
    candidate: CandidateConfig
    profile_path: Path
    criteria_path: Path
    profile_summary: str
    search: SearchConfig
    prefilter: PrefilterConfig = field(default_factory=PrefilterConfig)
    evaluator: EvaluatorConfig = field(default_factory=EvaluatorConfig)

    def load_profile(self) -> str:
        if not self.profile_path.exists():
            raise FileNotFoundError(
                f"{self.profile_path} not found. Create it with your resume/experience "
                "in Markdown — see profile.example.md for the expected structure."
            )
        return self.profile_path.read_text(encoding="utf-8")

    def load_criteria(self) -> str:
        if not self.criteria_path.exists():
            raise FileNotFoundError(
                f"{self.criteria_path} not found. Create it with your job search "
                "criteria in Markdown — see criteria.example.md for the expected structure."
            )
        return self.criteria_path.read_text(encoding="utf-8")

    def get_profile_summary(self) -> str:
        """Return the short profile summary written by the user in config.yaml.
        This is a one-time, user-authored (or LLM-generated during setup) blurb
        used only for the lightweight prefilter pass — kept separate from
        profile.md so the prefilter prompt stays short and precise regardless
        of how long the full profile is."""
        if not self.profile_summary or not self.profile_summary.strip():
            raise ValueError(
                "profile_summary is empty in config.yaml. Add a short (3-6 sentence) "
                "summary of your background — write it yourself, or generate it once "
                "with your LLM of choice by summarizing your profile.md."
            )
        return self.profile_summary.strip()


def _require(d: dict, key: str, section: str):
    if key not in d:
        raise KeyError(f"Missing required key '{key}' in '{section}' section of {CONFIG_PATH}")
    return d[key]


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Copy config.example.yaml to {path} and fill in "
            "your own candidate details, profile/criteria paths, and search preferences."
        )

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    candidate_raw = _require(raw, "candidate", "root")
    candidate = CandidateConfig(
        name=_require(candidate_raw, "name", "candidate"),
        email=_require(candidate_raw, "email", "candidate"),
        phone=_require(candidate_raw, "phone", "candidate"),
        location=_require(candidate_raw, "location", "candidate"),
    )

    search_raw = _require(raw, "search", "root")
    search = SearchConfig(
        terms=_require(search_raw, "terms", "search"),
        location=_require(search_raw, "location", "search"),
        results_per_call=search_raw.get("results_per_call", 25),
        hours_old=search_raw.get("hours_old", 240),
    )

    prefilter_raw = raw.get("prefilter", {})
    prefilter = PrefilterConfig(
        shortlist_min_size=prefilter_raw.get("shortlist_min_size", 30),
    )

    evaluator_raw = raw.get("evaluator", {})
    evaluator = EvaluatorConfig(top_n=evaluator_raw.get("top_n", 10))

    return AppConfig(
        candidate=candidate,
        profile_path=Path(raw.get("profile_path", "profile.md")),
        criteria_path=Path(raw.get("criteria_path", "criteria.md")),
        profile_summary=_require(raw, "profile_summary", "root"),
        search=search,
        prefilter=prefilter,
        evaluator=evaluator,
    )


_cached_config: AppConfig | None = None


def get_config(force_reload: bool = False) -> AppConfig:
    """Load config.yaml once and cache it. Pass force_reload=True to re-read from disk."""
    global _cached_config
    if _cached_config is None or force_reload:
        _cached_config = load_config()
    return _cached_config
