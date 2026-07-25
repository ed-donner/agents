"""
Gradio UI for the Platform Incident Copilot.

Run from this folder (so imports resolve):
  cd 4_langgraph/community_contributions/SamuelAdebodun
  python app.py

Requires OPENAI_API_KEY in the environment or a .env file (see load below).
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

from graph import PlatformIncidentCopilot, new_thread_id

_DEFAULT_CRITERIA = (
    "Include triage summary, likely causes, concrete validation steps, and when to escalate."
)


def _load_env() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    for candidate in (repo_root / ".env", Path(__file__).resolve().parent / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
    load_dotenv(override=False)


_load_env()

_DIR = Path(__file__).resolve().parent
_UI_EXAMPLE = _DIR / "ui_example.png"

_GRADIO_MAJOR = int(gr.__version__.split(".", 1)[0])

_APP_THEME = gr.themes.Default(primary_hue="orange")
_APP_CSS = """
        .criteria textarea { font-size: 0.95rem; }
        footer { display: none !important; }
        """


def _chatbot_kwargs() -> dict:
    """Gradio 6 removed show_copy_button; use buttons= instead."""
    base = {"label": "Conversation", "height": 380, "type": "messages"}
    if _GRADIO_MAJOR >= 6:
        base["buttons"] = ["copy"]
    else:
        base["show_copy_button"] = True
    return base


def _running_in_wsl() -> bool:
    return bool(os.environ.get("WSL_DISTRO_NAME")) or Path("/proc/sys/fs/binfmt_misc/WSLInterop").is_file()


def make_thread_id() -> str:
    return new_thread_id()


# Gradio 6 deep-copies `gr.State` defaults; LLM/httpx graphs are not copyable. Keep one copilot
# per process (LangGraph threads still isolate conversations via thread_id).
_copilot: PlatformIncidentCopilot | None = None


def _get_copilot() -> PlatformIncidentCopilot:
    global _copilot
    if _copilot is None:
        _copilot = PlatformIncidentCopilot()
    return _copilot


def _reset_copilot() -> None:
    global _copilot
    _copilot = PlatformIncidentCopilot()


async def process_message(
    message: str,
    success_criteria: str,
    history: list,
    thread: str,
):
    if not (message or "").strip():
        return history, thread
    copilot = _get_copilot()
    result = await copilot.arun_turn(message, success_criteria, thread)
    msgs = result["messages"]
    if len(msgs) < 2:
        return history, thread
    assistant_reply = msgs[-2]
    evaluator_msg = msgs[-1]
    user = {"role": "user", "content": message.strip()}
    reply = {"role": "assistant", "content": getattr(assistant_reply, "content", str(assistant_reply))}
    feedback = {"role": "assistant", "content": getattr(evaluator_msg, "content", str(evaluator_msg))}
    return history + [user, reply, feedback], thread


async def reset_session():
    _reset_copilot()
    return "", _DEFAULT_CRITERIA, None, make_thread_id()


def build_ui():
    # Gradio 6: theme/css belong on launch(), not Blocks().
    blocks_kw: dict = {"title": "Platform Incident Copilot"}
    if _GRADIO_MAJOR < 6:
        blocks_kw["theme"] = _APP_THEME
        blocks_kw["css"] = _APP_CSS

    with gr.Blocks(**blocks_kw) as ui:
        gr.Markdown(
            """
## Platform Incident Copilot

Paste an alert, log snippet, or ticket. The graph runs a **worker** (with lightweight
triage tools), then an **evaluator** with structured output—looping until the answer
meets your success criteria or the model asks you for more detail.

Set **OPENAI_API_KEY** before launching. No browser automation or cluster access is required.
"""
        )

        with gr.Accordion("Example run (screenshot submitted with this exercise)", open=False):
            if _UI_EXAMPLE.is_file():
                gr.Image(
                    value=str(_UI_EXAMPLE),
                    label="Sample session: Docker build failing at npm run build",
                    interactive=False,
                    show_label=True,
                )
            else:
                gr.Markdown(
                    "Place **`ui_example.png`** beside `app.py` to show the reference screenshot "
                    "(same image as in `week4_platform_incident.ipynb`)."
                )

        thread_state = gr.State(str(uuid.uuid4()))

        chatbot = gr.Chatbot(**_chatbot_kwargs())

        with gr.Row():
            message = gr.Textbox(
                label="Incident text",
                placeholder="e.g. Ingress returns 502 for checkout since 14:12 UTC; last deploy was payments-api 45m ago…",
                lines=4,
            )

        with gr.Row():
            success_criteria = gr.Textbox(
                label="Success criteria",
                elem_classes=["criteria"],
                value=_DEFAULT_CRITERIA,
                lines=2,
            )

        with gr.Row():
            reset_btn = gr.Button("New incident (reset thread)", variant="secondary")
            go_btn = gr.Button("Run triage", variant="primary")

        inputs = [message, success_criteria, chatbot, thread_state]
        outputs = [chatbot, thread_state]

        go_btn.click(process_message, inputs, outputs)
        message.submit(process_message, inputs, outputs)
        reset_btn.click(
            reset_session,
            [],
            [message, success_criteria, chatbot, thread_state],
        )

    return ui


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set. Export it or add it to .env at the repo root.")

    demo = build_ui()
    launch_kw: dict = {"inbrowser": True}
    if _GRADIO_MAJOR >= 6:
        launch_kw["theme"] = _APP_THEME
        launch_kw["css"] = _APP_CSS

    # WSL: bind on all interfaces so Windows browser can reach 127.0.0.1:port from the host.
    if _running_in_wsl():
        launch_kw["server_name"] = "0.0.0.0"
        launch_kw.setdefault("inbrowser", False)
        print("WSL detected: open in Windows browser → http://localhost:<port> (see URL below).")

    demo.launch(**launch_kw)
