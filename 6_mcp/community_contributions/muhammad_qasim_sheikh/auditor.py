import os
import json
from dotenv import load_dotenv
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from database import write_audit
from audit import AuditResult

load_dotenv(override=True)
DEFAULT_MODEL = "o3-mini"

INSTRUCTIONS = """
You are a Content Quality Auditor.
You can use the 'full_audit' tool to analyze text for readability, SEO quality, tone, and plagiarism.
Respond with a short human-readable summary, then show the structured JSON results in a code block.
"""

async def run_audit_agent(user_query: str, client_session_timeout_seconds: int = 60):
    mcp_params = {"command": "uv", "args": ["run", "seo_audit_server.py"]}

    async with MCPServerStdio(
        params=mcp_params, client_session_timeout_seconds=client_session_timeout_seconds
    ) as mcp:
        with trace("content_quality_auditor"):
            agent = Agent(
                name="content_quality_auditor",
                instructions=INSTRUCTIONS,
                model=DEFAULT_MODEL,
                mcp_servers=[mcp],
            )
            result = await Runner.run(agent, user_query)
            output = result.final_output

            json_part = None
            if "{" in output and "}" in output:
                try:
                    json_str = output.split("```json")[-1].split("```")[0]
                    json_part = json.loads(json_str)
                except Exception:
                    json_part = None

            if json_part:
                try:
                    audit_result = AuditResult(**json_part)
                    title = json_part.get("seo", {}).get("title", "Untitled")
                    content_preview = json_part.get("summary", "")[:500]
                    write_audit(
                        title=title,
                        content=content_preview,
                        overall_score=audit_result.overall_score,
                        report=audit_result.to_dict(),
                    )
                    print("[INFO] Audit saved to database")
                except Exception as e:
                    print(f"[WARN] Could not save audit: {e}")
            else:
                print("[WARN] No JSON found in LLM response, skipping database save.")

            return output
