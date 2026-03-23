import os
from dotenv import load_dotenv
from agents import Agent, OpenAIChatCompletionsModel, WebSearchTool
from openai import AsyncOpenAI
from models import SecurityAuditOutput
from guardrails import security_audit_guardrail

load_dotenv(override=True)

client = AsyncOpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL"), api_key=os.environ.get("OPENROUTER_API_KEY"))
model = OpenAIChatCompletionsModel(model=os.environ.get("CLAUDE_MODEL"), openai_client=client)

tools = [
    WebSearchTool(search_context_size="low"),
]

INSTRUCTIONS = """
Analyze the code_map and chunks for security vulnerabilities only.
Approach the code adversarially.

Look for: hardcoded secrets, SQL/command injection, insecure deserialization,
path traversal, weak cryptography, missing auth checks, eval()/exec() with
dynamic input, insecure HTTP, and exposed debug modes.
Use WebSearchTool to verify CVEs at nvd.nist.gov, osv.dev, or github.com/advisories.

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
)