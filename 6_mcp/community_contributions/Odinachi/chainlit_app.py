"""
Chainlit UI for the Odinachi multi-agent health navigator.

From repository root:
  uv run chainlit run 6_mcp/community_contributions/Odinachi/chainlit_app.py -w

Requires OPENAI_API_KEY. Optional: BRAVE_API_KEY, ODINACHI_HEALTH_MODEL.
"""

from __future__ import annotations

import os

import chainlit as cl
from dotenv import load_dotenv

load_dotenv(override=True)

from health_agents import DEFAULT_MODEL, run_health_navigator


def _session_stem() -> str:
    sid = getattr(cl.context.session, "id", None) or "default"
    safe = "".join(c if c.isalnum() else "_" for c in str(sid))
    return f"cl_{safe}"[:80]


@cl.on_chat_start
async def on_chat_start() -> None:
    await cl.Message(
        content=(
            "### Health intake navigator (educational)\n\n"
            "This assistant helps organize symptoms and points to **public** health information. "
            "It is **not** medical advice, diagnosis, or treatment. "
            "For emergencies, use your local emergency number.\n\n"
            "Describe what is going on; you can answer follow-up questions in later messages."
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    if not (message.content or "").strip():
        await cl.Message(content="Please describe your concern in a few words.").send()
        return

    model = os.getenv("ODINACHI_HEALTH_MODEL", DEFAULT_MODEL)
    placeholder = cl.Message(content="Working with intake tools and specialists…")
    await placeholder.send()

    try:
        reply = await run_health_navigator(
            message.content.strip(),
            session_stem=_session_stem(),
            model=model,
        )
    except Exception as e:
        reply = f"Something went wrong: {e!s}"

    placeholder.content = reply or "(No response text returned.)"
    await placeholder.update()
