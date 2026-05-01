import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI
from tools import write_report_tool
from models import ReportCompilerOutput
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("GPT_MODEL"), openai_client=client)

report_storage_params = {"command": "uv", "args": ["run", "mcp_servers/report_storage/server.py"], "env": {**os.environ}}
report_storage_mcp = MCPServerStdio(params=report_storage_params, client_session_timeout_seconds=30)

tools = [
    write_report_tool,
]

INSTRUCTIONS = """
Compile all findings into a Markdown report using write_report_tool.

Structure:
1. Executive Summary — date, file count, line count, finding counts,
   health score /10, one paragraph assessment.
2. Bug Findings — grouped CRITICAL → HIGH → MEDIUM → LOW.
3. Refactor Suggestions — grouped HIGH → MEDIUM → LOW.
4. Security Vulnerabilities — grouped CRITICAL → HIGH → MEDIUM → LOW.
5. Files Reviewed — table of file path, line count, parse status.
6. Action Plan — prioritized list across all categories,
   CRITICAL security issues always first.

- Report exactly what you received. Do not add or omit findings.
- If a category is empty, note it briefly.
- Return the report path and executive summary to the Orchestrator."""

report_compiler_agent = Agent(
    name="Report Compiler Agent",
    instructions=INSTRUCTIONS,
    output_type=ReportCompilerOutput,
    model=model,
    tools=tools,
    mcp_servers=[report_storage_mcp],
)