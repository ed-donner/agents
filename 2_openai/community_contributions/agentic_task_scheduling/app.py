"""
Gradio UI for the Task Scheduling Agent.(Run with: uv run app.py)
"""

import asyncio
import os
import sys
import traceback
import uuid
import gradio as gr

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from db import init_db, get_all_tasks, DB_PATH
from agents_workflow import chat, clear_session

# Initialise DB immediately
init_db()
print(f"[app] DB path: {DB_PATH}")

# Helpers

def format_tasks_table() -> str:
    """Read tasks directly from SQLite and return markdown string."""
    try:
        tasks = get_all_tasks()
        print(f"[refresh] DB={DB_PATH}  found {len(tasks)} task(s)")
        if not tasks:
            return "_No tasks scheduled yet._"
        rows = [
            "| ID | Title | Date | Time | Duration | Priority |",
            "|---|---|---|---|---|---|",
        ]
        for t in tasks:
            h = int(t["time"][:2])
            m = t["time"][3:]
            h12 = h % 12 or 12
            ampm = "AM" if h < 12 else "PM"
            rows.append(
                f"| {t['id']} | {t['title']} | {t['date']} "
                f"| {h12}:{m} {ampm} | {t['duration_minutes']} min "
                f"| {t['priority']} |"
            )
        return "\n".join(rows)
    except Exception as e:
        return f"Error reading tasks: {e}"


def respond(user_msg: str, history: list, session_id: str):
    if not user_msg.strip():
        return history, format_tasks_table()
    try:
        response = asyncio.run(chat(user_msg, session_id))
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[chat error]\n{tb}")
        response = f"Agent error: {e}\n\nCheck terminal for details."
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": response})
    return history, format_tasks_table()


def clear_textbox():
    return ""


def refresh_tasks():
    result = format_tasks_table()
    print(f"[refresh_btn] returning: {result[:80]}")
    return result


def reset_conversation(session_id: str):
    clear_session(session_id)
    return [], format_tasks_table()


# User Interface
EXAMPLES = [
    "Schedule a team standup tomorrow at 9am for 30 minutes",
    "Add an urgent task: fix production bug today at 2pm, 90 minutes",
    "I need to review the Q4 report this Friday afternoon",
    "Show all my tasks",
    "Delete task 3",
]

with gr.Blocks(title="Task Scheduler Agent") as demo:
    session_id_state = gr.State(lambda: str(uuid.uuid4()))

    gr.Markdown("## Task Scheduling Agent")
    gr.Markdown(
        "Chat to schedule tasks. Priority is detected automatically. "
        "Conflicts are handled with alternatives or rescheduling."
    )

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(height=480, show_label=False, type="messages")
            with gr.Row():
                msg_box = gr.Textbox(
                    placeholder="e.g. Schedule a 1-hour meeting tomorrow at 10am",
                    show_label=False,
                    scale=5,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            gr.Examples(examples=EXAMPLES, inputs=msg_box, label="Quick examples")
            clear_btn = gr.Button("Clear conversation", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### Scheduled Tasks")
            tasks_display = gr.Markdown(value=format_tasks_table())
            refresh_btn = gr.Button("Refresh", size="sm")

    send_btn.click(
        respond,
        inputs=[msg_box, chatbot, session_id_state],
        outputs=[chatbot, tasks_display],
    ).then(clear_textbox, inputs=[], outputs=[msg_box])

    msg_box.submit(
        respond,
        inputs=[msg_box, chatbot, session_id_state],
        outputs=[chatbot, tasks_display],
    ).then(clear_textbox, inputs=[], outputs=[msg_box])

    clear_btn.click(
        reset_conversation,
        inputs=[session_id_state],
        outputs=[chatbot, tasks_display],
    )

    refresh_btn.click(
        fn=refresh_tasks,
        inputs=[],
        outputs=[tasks_display],
    )

if __name__ == "__main__":
    demo.launch(share=False)