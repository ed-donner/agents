"""The two models the agent loop uses, kept in one place so they are easy to swap.

The orchestrator (Google ADK) authors the shared look and the hub page and runs
the QA checks; the five workers build the calculators. The orchestrator uses the
lighter Gemini model, whose rate limits comfortably fit the five parallel QA
agents; the commented alternatives are the bigger or cheaper choices (or set the
matching env var for a one-off run).
"""

import os

ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.1-flash-lite")  # bigger: gemini-3.5-flash
WORKER_MODEL = os.environ.get("WORKER_MODEL", "gpt-5.5")  # cheaper: gpt-5.4-mini
