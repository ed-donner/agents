import gradio as gr

from sidekick import Sidekick


async def setup():
    sk = Sidekick()
    await sk.setup()
    return sk


async def process_message(sidekick, session_context, message, success_criteria, history):
    if history is None:
        history = []
    results = await sidekick.run_superstep(
        message,
        success_criteria,
        history,
        session_context=session_context or "",
    )
    return results, sidekick


async def reset():
    sk = Sidekick()
    await sk.setup()
    return "", "", "", None, sk


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="teal")) as ui:
    gr.Markdown("## Sidekick")
    sidekick_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Chat", height=360, type="messages")
    session_context = gr.Textbox(
        label="Session context",
        placeholder="Optional: timezone, stack, tone, or constraints that apply to every turn.",
        lines=2,
    )
    message = gr.Textbox(label="Request", placeholder="What should get done?")
    success_criteria = gr.Textbox(
        label="Success criteria",
        placeholder="How you will judge completion.",
    )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go", variant="primary")

    ui.load(setup, [], [sidekick_state])
    go_button.click(
        process_message,
        [sidekick_state, session_context, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    message.submit(
        process_message,
        [sidekick_state, session_context, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    success_criteria.submit(
        process_message,
        [sidekick_state, session_context, message, success_criteria, chatbot],
        [chatbot, sidekick_state],
    )
    reset_button.click(
        reset, [], [session_context, message, success_criteria, chatbot, sidekick_state]
    )


if __name__ == "__main__":
    ui.launch(inbrowser=True)
