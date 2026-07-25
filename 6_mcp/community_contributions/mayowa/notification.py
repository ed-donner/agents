import os
from pathlib import Path
import sys

from agents import Agent, ModelSettings, Runner
from agents.mcp import MCPServerStdio


INSTRUCTIONS = """
You send a single push notification when research is complete.

Rules:
- Use the available push notification MCP tool exactly once.
- You MUST keep the message short and informative.
- Mention that the research is complete and include the topic.
- Do NOT send the full report in the notification.
"""


class Notification:
    @classmethod
    async def push(cls, report: str):
        push_server_path = Path(__file__).resolve().parent / "push_server.py"
        params = {
            "command": sys.executable,
            "args": [str(push_server_path)],
            "env": {
                "PUSHOVER_USER": os.getenv("PUSHOVER_USER", ""),
                "PUSHOVER_TOKEN": os.getenv("PUSHOVER_TOKEN", ""),
            },
        }
        preview = " ".join(report.split())[:200]
        message = (
            f"Research complete for: {report[:80]}. "
            f"Preview of report: {preview}"
        )

        async with MCPServerStdio(params=params, client_session_timeout_seconds=50) as server:
            agent = Agent(
                name="Notification",
                instructions=INSTRUCTIONS,
                model="gpt-4o-mini",
                mcp_servers=[server],
                model_settings=ModelSettings(tool_choice="required"),
            )
            await Runner.run(agent, message)
