"""Load env and app constants. Import this module first so dotenv runs before other app code."""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

# Walk upward from this file's directory (plan.md §13 O7).
load_dotenv(find_dotenv())


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")

# Model names (centralized; align with experiment.ipynb)
MODEL_TRIAGE = "gpt-4o-mini"
MODEL_CLARIFIER = "gpt-4o-mini"
MODEL_PLANNER = "gpt-5-nano"
MODEL_RESEARCH = "gpt-4o-mini"
MODEL_REPORT = "gpt-4o-mini"
MODEL_EVALUATOR = "gpt-4o-mini"

# Agent run limits
MAX_RESEARCH_TURNS = 20
DEFAULT_PHRASES_COUNT = 5
MAX_TRIAGE_ROUNDS = 3
# Evaluator: number of **retries** after the first failed evaluation (total rounds = 1 + this).
MAX_EVALUATOR_RETRIES = 2

# Manual QA only (unset or 0 for production). Not required in check_env.
# If both are set, EVALUATOR_DEBUG_ALWAYS_FAIL wins.
EVALUATOR_DEBUG_FAIL_ONCE = _env_truthy("EVALUATOR_DEBUG_FAIL_ONCE")
EVALUATOR_DEBUG_ALWAYS_FAIL = _env_truthy("EVALUATOR_DEBUG_ALWAYS_FAIL")

# Pushover (Phase H): short notification only; truncated to 300 chars before POST.
PUSHOVER_NOTIFY_MESSAGE = "Research job finished"
