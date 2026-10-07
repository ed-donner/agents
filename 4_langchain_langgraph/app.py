"""Gradio app for the Sidekick. Run with: uv run app.py"""

import html
import traceback

import gradio as gr

import styles
from sidekick import Sidekick


LAUNCH_STYLE = {
    "theme": styles.THEME,
    "css": styles.CSS,
    "head": styles.JS,
}

HEADER = """
<div id="header">
    <div class="context-label">Your personal co-worker</div>
    <h1>Sidekick</h1>
    <div class="brand-bar"></div>
</div>
"""

MODEL_CHOICES = {
    "OpenAI — GPT-5.4 mini": "openai:gpt-5.4-mini",
    "OpenAI — GPT-5.4": "openai:gpt-5.4",
}


def render_todos(todos):
    if not todos:
        items = (
            '<div class="placeholder">'
            "The Sidekick will write its plan here as it works"
            "</div>"
        )
    else:
        items = "<ul>" + "".join(
            f'<li class="{todo["status"]}">'
            f'<span class="mark"></span>'
            f'{html.escape(todo["content"])}'
            "</li>"
            for todo in todos
        ) + "</ul>"

    return f"<h3>Plan</h3>{items}"


async def setup(model):
    try:
        sidekick = Sidekick(
            model=MODEL_CHOICES[model]
        )

        await sidekick.setup()

        return (
            sidekick,
            gr.update(interactive=True),
        )

    except Exception:
        print("\n===== SIDEKICK SETUP FAILED =====")
        traceback.print_exc()
        print("=================================\n")
        raise

async def process_message(
    sidekick,
    message,
    success_criteria,
    history,
):
    try:
        if sidekick is None:
            return (
                history,
                gr.update(visible=False),
                sidekick,
            )

        print("\n>>> PROCESS MESSAGE STARTED")
        print(">>> Request:", message)

        results = await sidekick.run_turn(
            message,
            success_criteria,
            history,
        )

        print(">>> PROCESS MESSAGE COMPLETED")

        return (
            results,
            gr.update(visible=sidekick.paused),
            sidekick,
        )

    except Exception:
        print("\n===== PROCESS MESSAGE FAILED =====")
        traceback.print_exc()
        print("==================================\n")
        raise
    


async def approve(sidekick, history):
    results = await sidekick.resume(history)

    return (
        results,
        gr.update(visible=sidekick.paused),
        sidekick,
    )


def watch_todos(sidekick):
    """
    Called by the timer.

    The timer is the plan panel's only writer so live updates can
    render while the Sidekick is working.
    """

    if sidekick:
        return render_todos(sidekick.todos)

    return render_todos([])


async def reset(sidekick, model):
    try:
        if sidekick:
            sidekick.cleanup()

        new_sidekick = Sidekick(
            model=MODEL_CHOICES[model]
        )

        await new_sidekick.setup()

        return (
            "",                             # message
            "",                             # success criteria
            None,                           # chatbot
            gr.update(visible=False),       # approve button
            new_sidekick,                   # state
            gr.update(interactive=True),    # Go button
        )

    except Exception:
        print("\n===== SIDEKICK RESET FAILED =====")
        traceback.print_exc()
        print("=================================\n")
        raise


def free_resources(sidekick):
    if sidekick:
        sidekick.cleanup()


with gr.Blocks(
    title="Sidekick"
) as ui:

    gr.HTML(HEADER)

    model_selector = gr.Dropdown(
        choices=list(MODEL_CHOICES.keys()),
        value="OpenAI — GPT-5.4 mini",
        label="LLM (applied on Reset)",
        interactive=True,
    )

    sidekick = gr.State(
        delete_callback=free_resources
    )

    with gr.Row():

        chatbot = gr.Chatbot(
            label="Sidekick",
            height=320,
            scale=3,
            elem_id="chat",
        )

        with gr.Column(scale=1):

            todos_panel = gr.HTML(
                render_todos([]),
                elem_id="plan-panel",
            )

    with gr.Group(
        elem_id="ask-panel"
    ):

        with gr.Row():

            message = gr.Textbox(
                show_label=False,
                placeholder="Your request to the Sidekick",
            )

        with gr.Row():

            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="What are your success criteria?",
            )

    with gr.Row():

        reset_button = gr.Button(
            "Reset",
            elem_id="reset-button",
        )

        approve_button = gr.Button(
            "Approve and continue",
            visible=False,
            elem_id="approve-button",
        )

        go_button = gr.Button(
            "Go!",
            elem_id="go-button",
            interactive=False,
        )

    timer = gr.Timer(1)

    # Initial Sidekick setup when page loads
    ui.load(
        setup,
        inputs=[
            model_selector,
        ],
        outputs=[
            sidekick,
            go_button,
        ],
    )

    # Keep plan panel updated
    timer.tick(
        watch_todos,
        inputs=[
            sidekick,
        ],
        outputs=[
            todos_panel,
        ],
        show_progress="hidden",
    )

    # Enter in task field
    message.submit(
        process_message,
        inputs=[
            sidekick,
            message,
            success_criteria,
            chatbot,
        ],
        outputs=[
            chatbot,
            approve_button,
            sidekick,
        ],
    )

    # Enter in success criteria field
    success_criteria.submit(
        process_message,
        inputs=[
            sidekick,
            message,
            success_criteria,
            chatbot,
        ],
        outputs=[
            chatbot,
            approve_button,
            sidekick,
        ],
    )

    # Go button
    go_button.click(
        process_message,
        inputs=[
            sidekick,
            message,
            success_criteria,
            chatbot,
        ],
        outputs=[
            chatbot,
            approve_button,
            sidekick,
        ],
    )

    # Human approval
    approve_button.click(
        approve,
        inputs=[
            sidekick,
            chatbot,
        ],
        outputs=[
            chatbot,
            approve_button,
            sidekick,
        ],
    )

    # Reset Sidekick and apply selected model
    reset_button.click(
        reset,
        inputs=[
            sidekick,
            model_selector,
        ],
        outputs=[
            message,
            success_criteria,
            chatbot,
            approve_button,
            sidekick,
            go_button,
        ],
    )


if __name__ == "__main__":
    ui.launch(
        inbrowser=True,
        **LAUNCH_STYLE,
    )