from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv(override=True)

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = OpenAI(base_url=ANTHROPIC_BASE_URL, api_key=ANTHROPIC_API_KEY)
MODEL = "claude-haiku-4-5"



# Token budgets
CLARIFIER_MAX_TOKENS = int(os.getenv("CLARIFIER_MAX_TOKENS", "150"))
RESEARCH_MAX_TOKENS = int(os.getenv("RESEARCH_MAX_TOKENS", "250"))
RISK_MAX_TOKENS = int(os.getenv("RISK_MAX_TOKENS", "250"))
FINANCE_MAX_TOKENS = int(os.getenv("FINANCE_MAX_TOKENS", "250"))
PDF_MAX_TOKENS = int(os.getenv("PDF_MAX_TOKENS", "1800"))


DEFAULT_API_KWARGS = {
    "model": MODEL,
}
