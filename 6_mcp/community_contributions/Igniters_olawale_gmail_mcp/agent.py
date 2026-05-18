import asyncio
import os

from agents import Agent, OpenAIChatCompletionsModel, RunConfig, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv(override=True)

GMAIL_MCP_PARAMS = {
    "command": "uv",
    "args": [
        "run",
        "--directory",
        "/Users/admin/Documents/ai_engineering/gmail-mcp",
        "gmail",
        "--creds-file-path",
        "/Users/admin/.gmail-mcp/credentials.json",
        "--token-path",
        "/Users/admin/.gmail-mcp/tokens.json",
    ],
    "cwd": "/Users/admin/Documents/ai_engineering/gmail-mcp",
    "env": dict(os.environ),
}

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = "openai/gpt-4o-mini"

openrouter_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)


def instructions() -> str:
    return """You are a Gmail assistant. Use the Gmail MCP tools to send email, read email, search emails, list labels,
and any other tools the server exposes. Confirm actions briefly and report outcomes to the user."""


def run_config() -> RunConfig:
    return RunConfig(
        model=OpenAIChatCompletionsModel(
            model=MODEL,
            openai_client=openrouter_client,
        )
    )


async def run_agent_async(user_input: str) -> str:
    async with MCPServerStdio(
        params=GMAIL_MCP_PARAMS,
        client_session_timeout_seconds=120,
    ) as mcp_server:
        agent = Agent(
            name="GmailAssistant",
            instructions=instructions(),
            mcp_servers=[mcp_server],
        )

        try:
            result = await Runner.run(
                agent,
                user_input,
                max_turns=30,
                run_config=run_config(),
            )
            return str(result.final_output) if result.final_output else "No response"

        except Exception as e:
            return f"Error: {str(e)}"


def run_agent(user_input: str) -> str:
    return asyncio.run(run_agent_async(user_input))
