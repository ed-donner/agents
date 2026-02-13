"""Configuration for Jira Crew: Ollama (default) or Gemini LLM, and Jira API (MCP-style)."""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# LLM: local Ollama by default
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").strip().lower() in ("true", "1", "yes")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Gemini (only when USE_OLLAMA=false)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or ""

# Jira Cloud (optional – MCP tools work in read-only mode without credentials)
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://your-domain.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL") or ""
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN") or ""

def jira_configured() -> bool:
    return bool(JIRA_BASE_URL and "your-domain" not in JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN)
