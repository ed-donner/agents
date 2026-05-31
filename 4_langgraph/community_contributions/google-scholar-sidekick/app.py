# Install google-search-results>=2.4.2
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime


_APP_DIR = Path(__file__).resolve().parent
if str(_APP_DIR) not in sys.path:
    sys.path.insert(0, str(_APP_DIR))

from dotenv import load_dotenv

# Repo root .env when launching via `uv run python .../app.py` from agents/
load_dotenv(_APP_DIR / ".env")
load_dotenv(_APP_DIR.parents[3] / ".env")
load_dotenv()

import gradio as gr

from sidekick import Sidekick


async def setup():
    sk = Sidekick()
    await sk.setup()
    return sk


async def process_message(sidekick, message, success_criteria, history):
    print(f"[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] Processing message: {message}")
    if sidekick is None:
        sidekick = Sidekick()
        await sidekick.setup()
    text = (message or "").strip()
    if not text:
        return history or [], sidekick
    results = await sidekick.run_superstep(text, success_criteria, history or [])
    return results, sidekick


async def reset():
    new_sk = Sidekick()
    await new_sk.setup()
    return "", "", [], new_sk


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Google Scholar Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown(
        "## Google Scholar Sidekick\n"
        "Ask for papers on a topic. Set **success criteria** (e.g. recent sources with links). "
        "Requires `OPENAI_API_KEY`"
    )
    sidekick_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Scholar assistant", height=400, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="e.g. Latest papers on federated learning for healthcare",
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria (e.g. titles, years, and links)",
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick_state])
    message.submit(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    success_criteria.submit(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    go_button.click(
        process_message,
        [sidekick_state, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick_state])


if __name__ == "__main__":
    ui.queue()
    ui.launch(inbrowser=True)