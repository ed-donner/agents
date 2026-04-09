"""Gradio UI: isolated thread IDs + SQLite-backed LangGraph runs."""

from __future__ import annotations

import os
import sys
from typing import Optional

import gradio as gr
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

# Ensure this folder is on path when executed from repo root
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from graph import CareerSprintGraph, DEFAULT_SPRINT_CRITERIA, new_thread_id

load_dotenv(override=True)


def messages_to_chat_ui(messages: list[BaseMessage]) -> list[dict]:
    """Flatten LangChain messages into Gradio chatbot dicts."""
    out: list[dict] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"role": "user", "content": m.content or ""})
        elif isinstance(m, AIMessage):
            text = (m.content or "").strip() or "[model used tools]"
            out.append({"role": "assistant", "content": text})
        elif isinstance(m, ToolMessage):
            snippet = (m.content or "")[:1200]
            out.append({"role": "assistant", "content": f"_(tool result)_\n{snippet}"})
    return out


async def setup_app() -> tuple[CareerSprintGraph, str, list]:
    app = CareerSprintGraph()
    await app.setup()
    tid = new_thread_id()
    return app, tid, []


async def on_message(
    app: CareerSprintGraph,
    thread_id: str,
    lc_history: list[BaseMessage],
    user_text: str,
    success_criteria: str,
    company: str,
    role: str,
):
    if app is None:
        err = [
            {
                "role": "assistant",
                "content": "App is still loading. Wait until startup finishes, then try again.",
            }
        ]
        return err, lc_history, thread_id, app
    if not user_text or not str(user_text).strip():
        return gr.update(), lc_history, thread_id, app

    result = await app.run_turn(
        user_text.strip(),
        success_criteria,
        company,
        role,
        lc_history,
        thread_id,
    )
    new_lc: list[BaseMessage] = list(result["messages"])
    chat = messages_to_chat_ui(new_lc)
    return chat, new_lc, thread_id, app


async def on_reset(_app: Optional[CareerSprintGraph]):
    """New graph instance + thread so prior checkpoints do not leak into the next demo."""
    new_app = CareerSprintGraph()
    await new_app.setup()
    tid = new_thread_id()
    if _app is not None:
        await _app.aclose()
    return (
        new_app,
        tid,
        [],
        [],
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=""),
        gr.update(value=DEFAULT_SPRINT_CRITERIA),
    )


def main() -> None:
    with gr.Blocks(
        title="Career Sprint Sidekick",
        theme=gr.themes.Default(primary_hue="teal"),
    ) as demo:
        gr.Markdown(
            "## Career Sprint Sidekick\n"
            "LangGraph + tools + rubric loop + SQLite checkpoints. "
            "Optional **me/summary.txt** personalizes output. Writes packs under **sandbox/**."
        )
        app_state = gr.State()
        thread_state = gr.State()
        lc_state = gr.State([])

        with gr.Row():
            company = gr.Textbox(label="Target company", placeholder="e.g. Acme Labs")
            role = gr.Textbox(label="Target role", placeholder="e.g. Backend Engineer")
        success_criteria = gr.Textbox(
            label="Success criteria (optional)",
            lines=4,
            value=DEFAULT_SPRINT_CRITERIA,
        )
        chat = gr.Chatbot(label="Sprint thread", height=420)
        user_in = gr.Textbox(
            label="Your message",
            placeholder="Describe the sprint, e.g. research + talking points + outreach note...",
            lines=2,
        )
        with gr.Row():
            go = gr.Button("Run sprint turn", variant="primary")
            reset = gr.Button("New session", variant="secondary")

        demo.load(
            setup_app,
            [],
            [app_state, thread_state, lc_state],
            time_limit=180,
        )

        go.click(
            on_message,
            [app_state, thread_state, lc_state, user_in, success_criteria, company, role],
            [chat, lc_state, thread_state, app_state],
            time_limit=600,
            show_progress="minimal",
        )
        user_in.submit(
            on_message,
            [app_state, thread_state, lc_state, user_in, success_criteria, company, role],
            [chat, lc_state, thread_state, app_state],
            time_limit=600,
            show_progress="minimal",
        )
        reset.click(
            on_reset,
            [app_state],
            [app_state, thread_state, lc_state, chat, user_in, company, role, success_criteria],
            time_limit=180,
        )

    demo.queue()

    host = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name=host, server_port=port, share=False)


if __name__ == "__main__":
    main()
