import gradio as gr
from sidekick import Sidekick

IDLE_STATUS = ""
WAITING_STATUS = "⏳ **Forge is waiting for your reply** — answer the question above and hit Go!"


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    history, awaiting_clarification = await sidekick.run_superstep(
        message, success_criteria, history
    )
    status = WAITING_STATUS if awaiting_clarification else IDLE_STATUS
    placeholder = (
        "Reply to Forge's question above..."
        if awaiting_clarification
        else "What do you need? e.g. 'Debug this error: ...' or 'Find the docs for ...' or 'Draft an email to ...'"
    )
    return history, sidekick, status, gr.update(placeholder=placeholder)


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return (
        "",
        "",
        None,
        new_sidekick,
        IDLE_STATUS,
        gr.update(placeholder="What do you need? e.g. 'Debug this error: ...' or 'Find the docs for ...' or 'Draft an email to ...'"),
    )


def free_resources(sidekick):
    print("Cleaning up Forge...")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Forge", theme=gr.themes.Default(primary_hue="orange")) as ui:
    gr.Markdown("## Forge — Your Engineering Sidekick")
    gr.Markdown(
        "Ask Forge to **debug an issue**, **look up docs**, or **draft an email**. "
        "Set success criteria to tell Forge exactly when it's done."
    )
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Forge", height=400, type="messages")

    status_display = gr.Markdown(value=IDLE_STATUS)

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="What do you need? e.g. 'Debug this error: ...' or 'Find the docs for ...' or 'Draft an email to ...'"
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria (optional) e.g. 'Provide a working fix with explanation' or 'Draft saved to sandbox/'"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])

    for trigger in [message.submit, success_criteria.submit, go_button.click]:
        trigger(
            process_message,
            [sidekick, message, success_criteria, chatbot],
            [chatbot, sidekick, status_display, message],
        )

    reset_button.click(
        reset,
        [],
        [message, success_criteria, chatbot, sidekick, status_display, message],
    )


ui.launch(inbrowser=True)
