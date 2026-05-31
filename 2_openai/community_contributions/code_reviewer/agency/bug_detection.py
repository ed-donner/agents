import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from models import BugDetectionOutput
from guardrails import bug_detection_guardrail
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("CLAUDE_MODEL"), openai_client=client)

test_runner_params = {"command": "uv", "args": ["run", "mcp_servers/test_runner/server.py"], "env": {**os.environ}}
test_runner_mcp = MCPServerStdio(params=test_runner_params, client_session_timeout_seconds=30)

INSTRUCTIONS = """
Analyze the code_map and chunks for bugs and runtime issues only.
Do not report style or security concerns.

Look for: logical errors, null dereferences, missing error handling, type
misuse, resource leaks, race conditions, infinite loops, mutable default
arguments, and incorrect API usage.

Return findings under the key "bugs". Each finding must include:
file_path, line_number, severity (CRITICAL/HIGH/MEDIUM/LOW),
category, description, suggestion.

- Every finding must cite a specific file and line number.
- Descriptions must be specific, never vague.
- Rank by severity: CRITICAL → HIGH → MEDIUM → LOW."""

bug_detection_agent = Agent(
    name="Bug Detection Agent",
    instructions=INSTRUCTIONS,
    output_type=BugDetectionOutput,
    model=model,
    output_guardrails=[bug_detection_guardrail],
    mcp_servers=[test_runner_mcp],
)