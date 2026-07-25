"""
Gradio entrypoint for the Nairobi LangGraph multi-agent demo.

From the agents repo root:

  uv run python 4_langgraph/community_contributions/makinda/nairobi_city_agents/app.py

Environment:
  OPENAI_API_KEY          — required
  SERPER_API_KEY          — required when the local DB has no events (or delete DB to force)
  OPENWEATHER_API_KEY  — recommended (current + ~36h forecast for outfit/activity advice)
  LANGSMITH_API_KEY       — optional; enables tracing 
  LANGCHAIN_API_KEY       — optional; same as LangSmith key
  LANGCHAIN_PROJECT       — optional; defaults to nairobi-city-agents
  LANGCHAIN_TRACING_V2    — optional; defaults to true when a LangSmith/LangChain key is set
"""

from __future__ import annotations

import uuid

import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

from config import langsmith_banner_markdown
from graph import run_once


def ask_nairobi(question: str):
    """Generator so the UI updates immediately, then shows the final Markdown."""
    busy = (
        "## Working on it…\n\n"
        "The **Nairobi LangGraph** pipeline is running:\n\n"
        "1. **Local events** — SQLite (LLM dummy seed if the DB is empty)  \n"
        "2. **Web search** — Serper only if local events are still missing  \n"
        "3. **Weather** — OpenWeatherMap current + short forecast  \n"
        "4. **Outfit & activities** — specialist pass from the forecast  \n"
        "5. **Venue RAG** — Chroma retrieval  \n"
        "6. **Final briefing** — combined analysis  \n\n"
        "*Usually ~30–90 seconds, depending on APIs and LLM latency.*"
    )
    yield busy

    q = (question or "").strip()
    if not q:
        q = "What is happening in Nairobi and what should I plan for given the weather?"
    try:
        result = run_once(q, thread_id=str(uuid.uuid4()))
    except Exception as exc:  # noqa: BLE001 — show errors in the UI
        result = f"**Run failed:** `{exc}`"
    yield result


def main() -> None:
    with gr.Blocks(title="Nairobi city agents (LangGraph)") as demo:
        gr.Markdown(
            "## Nairobi multi-agent workflow\n"
            "Local SQLite events → **LLM dummy seed** if empty → **Serper** if still empty → "
            "**OpenWeatherMap** (current + short forecast) → **outfit & activities advisor** → "
            "**Chroma RAG** (venues & rainy-season notes) → **final analysis**.\n\n"
            "Implemented with this course’s LangGraph patterns and OpenAI.\n\n"
            f"{langsmith_banner_markdown()}"
        )
        q = gr.Textbox(
            label="Your question",
            value="What's happening in Nairobi this week and how should I dress given the rain?",
            lines=3,
        )
        out = gr.Markdown()
        run_btn = gr.Button("Run graph", variant="primary")
        run_btn.click(
            fn=ask_nairobi,
            inputs=[q],
            outputs=[out],
            show_progress="full",
        )
    demo.queue()
    demo.launch()


if __name__ == "__main__":
    main()
