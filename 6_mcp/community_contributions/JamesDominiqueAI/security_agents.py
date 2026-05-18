from agents import Agent, Runner
from mcp_client import get_logs_tools_openai, get_network_tools_openai
from dotenv import load_dotenv
import json

load_dotenv(override=True)

MODEL = "gpt-4o-mini"


DETECTOR_PROMPT = """\
You are a security Detector agent. Your job is to scan system logs for anomalies.

Steps:
1. Call get_recent_logs() to fetch all available logs.
2. Call get_failed_logins(threshold=3) to find brute-force candidates.
3. Identify suspicious patterns: repeated failures, port scans, privilege escalation, unusual timings.
4. Output ONLY a JSON object with this schema (no markdown, no prose):
{
  "anomalies": [
    {
      "type": "<brute_force|port_scan|priv_escalation|other>",
      "src_ip": "<ip or null>",
      "user": "<username or null>",
      "event_count": <int>,
      "time_window": "<e.g. 2026-03-26 02:11:01 – 02:11:13>",
      "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "raw_events": [ ...relevant log entries... ]
    }
  ],
  "summary": "<one sentence describing what you found>"
}
"""

INVESTIGATOR_PROMPT = """\
You are a security Investigator agent. You receive a JSON report of anomalies from the Detector.

Steps:
1. For each anomaly that has a src_ip, call check_ip_reputation(ip) and get_traffic_summary(ip).
2. Call get_active_connections() to see the current network state.
3. Synthesise everything into a clear, human-readable incident report.

Your output must be a JSON object (no markdown fences):
{
  "incident_title": "<short title>",
  "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "what_happened": "<2-4 sentences explaining the attack chain>",
  "threat_actors": [
    { "ip": "<ip>", "reputation": "<reputation>", "role": "<role in attack>" }
  ],
  "timeline": "<narrative of events in chronological order>",
  "confidence": "<LOW|MEDIUM|HIGH>"
}
"""

RESPONDER_PROMPT = """\
You are a security Responder agent. You receive an investigation report and must recommend actions.

Produce ONLY a JSON object (no markdown fences):
{
  "immediate_actions": [
    "<action 1>",
    "<action 2>"
  ],
  "short_term_actions": [
    "<action 1>"
  ],
  "long_term_hardening": [
    "<recommendation 1>"
  ],
  "block_list": ["<ip1>", "<ip2>"],
  "escalate_to_human": <true|false>,
  "escalation_reason": "<reason or null>"
}

Be specific. Reference IPs, usernames, and services from the report. Keep each action concise.
"""



async def make_detector() -> Agent:
    logs_tools = await get_logs_tools_openai()
    return Agent(
        name="Detector",
        instructions=DETECTOR_PROMPT,
        model=MODEL,
        tools=logs_tools,
    )


async def make_investigator() -> Agent:
    network_tools = await get_network_tools_openai()
    return Agent(
        name="Investigator",
        instructions=INVESTIGATOR_PROMPT,
        model=MODEL,
        tools=network_tools,
    )


async def make_responder() -> Agent:
    return Agent(
        name="Responder",
        instructions=RESPONDER_PROMPT,
        model=MODEL,
        tools=[],
    )



async def run_pipeline(user_logs: str | None = None) -> dict:
    """
    Run the full Detector → Investigator → Responder pipeline.

    Args:
        user_logs: Optional raw log text provided by the user. If None, the
                   Detector fetches logs from the MCP server directly.

    Returns:
        dict with keys: detector, investigator, responder (each a parsed dict)
    """
    detector = await make_detector()
    if user_logs:
        detect_prompt = (
            f"Analyse the following logs for security anomalies:\n\n{user_logs}"
        )
    else:
        detect_prompt = "Fetch the recent logs and identify all security anomalies."

    detect_result = await Runner.run(detector, detect_prompt, max_turns=8)
    detect_output = detect_result.final_output

    investigator = await make_investigator()
    investigate_result = await Runner.run(
        investigator,
        f"Here is the anomaly report from the Detector:\n\n{detect_output}\n\n"
        "Enrich it with network intelligence and write the incident report.",
        max_turns=10,
    )
    investigate_output = investigate_result.final_output

    responder = await make_responder()
    respond_result = await Runner.run(
        responder,
        f"Here is the investigation report:\n\n{investigate_output}\n\n"
        "Produce the remediation action plan.",
        max_turns=5,
    )
    respond_output = respond_result.final_output

    def _safe_parse(text: str) -> dict:
        try:
            clean = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(clean)
        except Exception:
            return {"raw": text}

    return {
        "detector":     _safe_parse(detect_output),
        "investigator": _safe_parse(investigate_output),
        "responder":    _safe_parse(respond_output),
    }
