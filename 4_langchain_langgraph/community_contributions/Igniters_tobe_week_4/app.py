import gradio as gr

from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    snapshot = sidekick.get_status_snapshot()
    return sidekick, snapshot["status"], snapshot["progress_log"], snapshot["feedback"]


async def process_message(sidekick, message, success_criteria, history):
    history = history or []

    if sidekick is None:
        return (
            history
            + [
                {"role": "user", "content": message},
                {
                    "role": "assistant",
                    "content": "Sidekick is still initializing. Please wait and try again.",
                },
            ],
            sidekick,
            message,
            "Initializing",
            "Waiting for setup to finish.",
            "No evaluation yet.",
        )

    if not message or not message.strip():
        snapshot = sidekick.get_status_snapshot()
        return history, sidekick, "", snapshot["status"], snapshot["progress_log"], snapshot["feedback"]

    try:
        results = await sidekick.run_superstep(message, success_criteria, history)
        snapshot = sidekick.get_status_snapshot()
        return (
            results,
            sidekick,
            "",
            snapshot["status"],
            snapshot["progress_log"],
            snapshot["feedback"],
        )
    except Exception as exc:
        error_message = f"Error: {exc}"
        snapshot = sidekick.get_status_snapshot()
        return (
            history + [{"role": "user", "content": message}, {"role": "assistant", "content": error_message}],
            sidekick,
            "",
            "Error",
            snapshot["progress_log"] + "\n" + error_message,
            snapshot["feedback"],
        )


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    snapshot = new_sidekick.get_status_snapshot()
    return "", "", None, new_sidekick, snapshot["status"], snapshot["progress_log"], snapshot["feedback"]


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as exc:
        print(f"Cleanup error: {exc}")


with gr.Blocks(title="Igniters Tobe Week 4", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("Sidekick with guardrails, clarifying questions, and progress reporting")

    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=420, type="messages")

    with gr.Row():
        with gr.Column(scale=3):
            message = gr.Textbox(
                show_label=False,
                placeholder="Describe the task you want the Sidekick to complete.",
            )
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Optional success criteria. Example: produce a concise answer with sources.",
            )
        with gr.Column(scale=2):
            status_display = gr.Textbox(label="Current Status", interactive=False)
            feedback_display = gr.Textbox(label="Latest Evaluation", interactive=False, lines=4)
            progress_log = gr.Textbox(label="Progress Log", interactive=False, lines=12)

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick, status_display, progress_log, feedback_display])

    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, message, status_display, progress_log, feedback_display],
    )
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick, message, status_display, progress_log, feedback_display],
    )
    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, sidekick, status_display, progress_log, feedback_display],
    )


ui.launch(inbrowser=True)
