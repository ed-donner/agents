import asyncio
import os

import requests
from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

if not HA_URL or not HA_TOKEN:
    raise ValueError("Missing HA_URL or HA_TOKEN in .env")

INSTRUCTIONS = """
You are a news research agent.

Research today's major news from several reputable newspapers and news sources.

Select the 10 most important stories.

Create TWO outputs:

1. FULL REPORT
- Detailed Markdown
- 10 stories
- Each story should include:
  - headline
  - 1-2 sentence summary
  - source
- Finish with a section called "What matters today"
- Save this full version to sandbox/news.md

2. DASHBOARD SUMMARY
- Much shorter Markdown for a Home Assistant dashboard
- 10 stories
- Each story should contain:
  - short headline
  - one concise sentence only
  - source
- Finish with a very short "What matters today" section of 2-3 sentences

Return both outputs in this exact format:

===FULL_REPORT===
<full markdown>

===DASHBOARD===
<compact markdown>

Accept cookies and navigate pop-ups as needed.
If one website isn't fruitful, try another.
Be persistent until you have completed the assignment.
When writing files, write only inside the sandbox/ folder.
"""

TASK = """
Research today's major news and produce both outputs:
the full report and the compact dashboard summary.
"""

sandbox_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "sandbox"))
os.makedirs(sandbox_path, exist_ok=True)

files_params = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path],
}
playwright_params = {"command": "npx", "args": ["@playwright/mcp@latest"]}


async def main() -> None:
    async with MCPServerStdio(
        params=files_params,
        client_session_timeout_seconds=60,
    ) as mcp_server_files:
        async with MCPServerStdio(
            params=playwright_params,
            client_session_timeout_seconds=60,
        ) as mcp_server_browser:
            agent = Agent(
                name="investigator",
                instructions=INSTRUCTIONS,
                model="gpt-5.4-mini",
                mcp_servers=[
                    mcp_server_files,
                    mcp_server_browser,
                ],
            )

            with trace("investigate"):
                result = await Runner.run(
                    agent,
                    TASK,
                    max_turns=20,
                )

           
            output = result.final_output

            full_report = output.split("===FULL_REPORT===")[1].split("===DASHBOARD===")[0].strip()
            dashboard_markdown = output.split("===DASHBOARD===")[1].strip()

            print("\nFULL REPORT:\n")
            print(full_report)

            print("\nDASHBOARD SUMMARY:\n")
            print(dashboard_markdown)


    response = requests.post(
        f"{HA_URL}/api/states/sensor.ai_news",
        headers={
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json",
        },
        json={
            "state": "updated",
            "attributes": {
                "friendly_name": "AI News Summary",
                "markdown": dashboard_markdown,
            },
        },
    )

    response.raise_for_status()
    print("Home Assistant updated successfully.")


if __name__ == "__main__":
    asyncio.run(main())
