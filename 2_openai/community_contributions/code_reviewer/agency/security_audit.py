import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, WebSearchTool
from openai import AsyncOpenAI
from models import SecurityAuditOutput
from guardrails import security_audit_guardrail
from agents.mcp import MCPServerStdio

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("CLAUDE_MODEL"), openai_client=client)

cve_lookup_params = {"command": "uv", "args": ["run", "mcp_servers/cve_lookup/server.py"]}
cve_lookup_mcp = MCPServerStdio(params=cve_lookup_params, client_session_timeout_seconds=30)

tools = [
    WebSearchTool(search_context_size="low"),
]

INSTRUCTIONS = """
Analyze the code_map and chunks for security vulnerabilities only.
Approach the code adversarially.

Use cve_lookup MCP tools as the primary source for CVE verification.
Only fall back to WebSearchTool when the library is not found in NVD or OSV,
or when broader context about active exploitation is needed.

Look for: hardcoded secrets, SQL/command injection, insecure deserialization,
path traversal, weak cryptography, missing auth checks, eval()/exec() with
dynamic input, insecure HTTP, and exposed debug modes.

Return findings under the key "security_findings". Each entry must include:
file_path, line_number, severity (CRITICAL/HIGH/MEDIUM/LOW),
category, description, recommendation.

- Never reproduce actual secret values. Reference file and line only.
- CRITICAL is reserved for RCE, data breach, or full auth bypass.
- Rank by severity: CRITICAL → HIGH → MEDIUM → LOW."""

security_audit_agent = Agent(
    name="Security Audit Agent",
    instructions=INSTRUCTIONS,
    output_type=SecurityAuditOutput,
    model=model,
    tools=tools,
    output_guardrails=[security_audit_guardrail],
    mcp_servers=[cve_lookup_mcp],
)