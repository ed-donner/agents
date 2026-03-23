import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from models import RefactorSuggestionOutput

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("CLAUDE_MODEL"), openai_client=client)

INSTRUCTIONS = """
Analyze the code_map and chunks for code quality issues only.
Do not report bugs or security concerns.

Look for: duplicated logic, functions over 30 lines, poor naming, missing
docstrings or type hints, nesting beyond 3 levels, dead code, magic numbers,
Single Responsibility violations, and manual reimplementation of stdlib utilities.

Return findings under the key "refactor_suggestions". Each entry must include:
file_path, line_number, priority (HIGH/MEDIUM/LOW),
category, description, suggestion.

- Every suggestion must be specific and actionable.
- Rank by priority: HIGH → MEDIUM → LOW."""

refactor_suggestion_agent = Agent(
    name="Refactor Suggestion Agent",
    instructions=INSTRUCTIONS,
    output_type=RefactorSuggestionOutput,
    model=model,
)