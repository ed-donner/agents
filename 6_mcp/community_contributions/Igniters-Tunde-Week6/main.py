"""
Gradio host for the Habit streak MCP server (OpenAI Agents SDK + MCPServerStdio + Gemini).
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import gradio as gr
from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv
from openai import AsyncOpenAI

_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT.parent.parent.parent / ".env", override=False)

# Gemini-only: avoid "OPENAI_API_KEY is not set, skipping trace export" on every run.
set_tracing_disabled(True)

_SUBPROCESS_ENV = {k: v for k, v in os.environ.items() if v is not None}

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"

HABIT_MCP_PARAMS: dict = {
    "command": sys.executable,
    "args": [str(_ROOT / "mcp_habit_server.py")],
    "cwd": str(_ROOT),
    "env": _SUBPROCESS_ENV,
}

INSTRUCTIONS = """You are a concise habit coach. You MUST use the MCP tools to read or change data—do not invent streaks or logs.

Tools:
- log_habit(name, done, note="") — record today (local date). Overwrites if same habit already logged today.
- list_habits() — all habit names in the file.
- streak(name) — strict consecutive days ending today with done=True (missing day or done=False breaks).
- recent_days(name, days=7) — per-day done/note for the last N days.

After using tools, answer in plain language (short). If the user is vague, ask one clarifying question or suggest list_habits first.
"""


def _gemini_api_key() -> str:
    return (
        (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip().strip('"').strip("'")
    )


def _gemini_model_id() -> str:
    return (os.getenv("GEMINI_MODEL") or "gemini-2.0-flash").strip()


async def coach(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return "Say something like: **Log walk as done**, **What’s my read streak?**, or **List my habits**."

    api_key = _gemini_api_key()
    if not api_key:
        return (
            "Set **GEMINI_API_KEY** or **GOOGLE_API_KEY** in `.env` (this folder or repo root `agents/.env`) "
            "and restart. Optional: **GEMINI_MODEL** (default `gemini-2.0-flash`)."
        )

    gemini_client = AsyncOpenAI(base_url=GEMINI_OPENAI_BASE, api_key=api_key)
    model = OpenAIChatCompletionsModel(
        model=_gemini_model_id(),
        openai_client=gemini_client,
    )

    try:
        async with MCPServerStdio(
            params=HABIT_MCP_PARAMS,
            client_session_timeout_seconds=60,
        ) as mcp_server:
            agent = Agent(
                name="habit_coach",
                instructions=INSTRUCTIONS,
                model=model,
                mcp_servers=[mcp_server],
            )
            result = await Runner.run(agent, text)
            return result.final_output or "(no output)"
    except Exception as e:
        return f"Error: {e}"


def main():
    if not _gemini_api_key():
        print("Warning: GEMINI_API_KEY / GOOGLE_API_KEY not set. Add it to .env.")

    # Reduces noisy "Event loop is closed" from stdio pipes on Ctrl+C (Windows + MCP subprocess).
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    with gr.Blocks(title="Habit streak coach") as demo:
        gr.Markdown(
            "## Habit streak (MCP + **Gemini**)\n"
            "Chat with a coach that uses a **local MCP server** (`mcp_habit_server.py`) to "
            "**log habits**, **list habits**, **compute streaks**, and show **recent days**. "
            "LLM: **Google Gemini** (OpenAI-compatible API). Data: `habits_data.json` in this folder."
        )
        out = gr.Markdown()
        msg = gr.Textbox(
            label="Message",
            placeholder='Try: "Log meditation as done" or "What is my walk streak?"',
            lines=2,
        )
        btn = gr.Button("Send", variant="primary")
        btn.click(coach, msg, out)
        msg.submit(coach, msg, out)

    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
