"""Shared configuration."""

import os

from dotenv import load_dotenv

load_dotenv(override=True)

# OpenAI model for this course exercise
MODEL = os.environ.get("OPENAI_COURSE_MODEL", "gpt-4o-mini")

MAX_RESEARCH_LOOP_ITERATIONS = int(os.environ.get("MAX_RESEARCH_LOOP_ITERATIONS", "3"))

# Set USE_A2A_REMOTE=1 to call researcher / judge / content_builder over HTTP (based on a2a_services.py).
USE_A2A_REMOTE = os.environ.get("USE_A2A_REMOTE", "").lower() in ("1", "true", "yes")

RESEARCHER_BASE_URL = os.environ.get("RESEARCHER_AGENT_URL", "http://127.0.0.1:8001")
JUDGE_BASE_URL = os.environ.get("JUDGE_AGENT_URL", "http://127.0.0.1:8002")
CONTENT_BUILDER_BASE_URL = os.environ.get(
    "CONTENT_BUILDER_AGENT_URL", "http://127.0.0.1:8003"
)
