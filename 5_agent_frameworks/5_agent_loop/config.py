"""The two models the agent loop uses, kept in one place so they are easy to swap.

The orchestrator (Google ADK) authors the shared look and the hub page; the five
workers build the games. The demo uses the bigger models. To run cheaply, change
the two defaults below to the commented alternatives (or set the matching env var
for a one-off run).
"""

import os

ORCHESTRATOR_MODEL = os.environ.get("ORCHESTRATOR_MODEL", "gemini-3.5-flash")  # cheaper: gemini-3.1-flash-lite
WORKER_MODEL = os.environ.get("WORKER_MODEL", "gpt-5.5")  # cheaper: gpt-5.4-mini
