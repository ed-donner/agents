import uuid
from datetime import datetime
from pathlib import Path

import gradio as gr

from sidekick import Sidekick
from sidekick_tools import serper_warning_message

_CHRYS_DIR = Path(__file__).resolve().parent
_EXPORTS = _CHRYS_DIR / "exports"
_EXPORTS.mkdir(parents=True, exist_ok=True)


async def setup():
    sk = Sidekick()
    await sk.setup()
    warn = serper_warning_message()
    md = f"### Config\n{warn}" if warn else ""
    return sk, sk.sidekick_id, md


async def process_message(
    sidekick,
    message,
    success_criteria,
    history,
    skip_clarification,
):
    if not message or not message.strip():
        return history, sidekick, "", gr.update()
    new_hist, trace = await sidekick.run_superstep(
        message.strip(),
        success_criteria or "",
        history or [],
        skip_clarification=bool(skip_clarification),
    )
    return new_hist, sidekick, trace, gr.update()


async def reset():
    sk = Sidekick()
    await sk.setup()
    warn = serper_warning_message()
    md = f"### Config\n{warn}" if warn else ""
    return sk, sk.sidekick_id, md, None, "", "", gr.update(value=False)


def apply_thread_id(sidekick, text):
    if not sidekick or not text or not str(text).strip():
        return sidekick, gr.update()
    try:
        uuid.UUID(str(text).strip())
    except ValueError:
        return sidekick, gr.update()
    sidekick.set_thread_id(str(text).strip())
    return sidekick, gr.update(value=sidekick.sidekick_id)


def save_chat_to_file(history, success_criteria):
    if not history:
        return "Nothing to save."
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = _EXPORTS / f"sidekick_chat_{ts}.md"
    lines = ["# Sidekick export", "", f"**Success criteria:** {success_criteria or '(none)'}", ""]
    for m in history:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"## {role.upper()}\n\n{content}\n")
    path.write_text("\n".join(lines), encoding="utf-8")
    return f"Saved to {path}"


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"cleanup error: {e}")


with gr.Blocks(title="Chrys Sidekick") as ui:
    gr.Markdown("## Chrys sidekick — clarify → plan → research & tools")
    serper_md = gr.Markdown(visible=True)

    sidekick = gr.State(delete_callback=free_resources)
    thread_display = gr.Textbox(label="Thread ID (checkpoint)", interactive=False)

    with gr.Row():
        chatbot = gr.Chatbot(label="Chat", height=420, type="messages")
    with gr.Group():
        message = gr.Textbox(
            show_label=False,
            placeholder="Your message…",
            lines=2,
        )
        success_criteria = gr.Textbox(
            label="Success criteria",
            placeholder="What does “done” look like?",
            lines=2,
        )
    with gr.Row():
        skip_clar = gr.Checkbox(label="Skip clarification", value=False)
    with gr.Row():
        go_btn = gr.Button("Send", variant="primary")
        reset_btn = gr.Button("New conversation", variant="stop")
    with gr.Accordion("Tool trace (last turn)", open=False):
        trace_box = gr.Textbox(label="Tools", lines=6, interactive=False)
    with gr.Row():
        save_btn = gr.Button("Save chat to Markdown")
        save_status = gr.Textbox(show_label=False, interactive=False)
    with gr.Row():
        thread_in = gr.Textbox(
            label="Resume thread ID",
            placeholder="Paste UUID from a previous session",
        )
        apply_thread_btn = gr.Button("Apply thread ID")

    ui.load(setup, [], [sidekick, thread_display, serper_md])

    go_btn.click(
        process_message,
        [sidekick, message, success_criteria, chatbot, skip_clar],
        [chatbot, sidekick, trace_box, message],
    )
    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot, skip_clar],
        [chatbot, sidekick, trace_box, message],
    )
    reset_btn.click(
        reset,
        [],
        [sidekick, thread_display, serper_md, chatbot, message, success_criteria, skip_clar],
    )
    save_btn.click(
        save_chat_to_file,
        [chatbot, success_criteria],
        [save_status],
    )
    apply_thread_btn.click(
        apply_thread_id,
        [sidekick, thread_in],
        [sidekick, thread_display],
    )

if __name__ == "__main__":
    ui.launch(inbrowser=True)
