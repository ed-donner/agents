import gradio as gr
from sidekick import Sidekick


async def setup():
    try:
        sidekick = Sidekick()
        await sidekick.setup()
        return sidekick
    except Exception as e:
        print(f"Setup failed: {e}")
        raise


def add_user_message(message, history):
    if not message.strip():
        return "", history
    history = history + [{"role": "user", "content": message}]
    return "", history


async def get_response(sidekick, history):
    if sidekick is None:
        return history + [{"role": "assistant", "content": "Setup failed. Please reset and try again."}], sidekick
    user_msg = history[-1]["content"]
    history, needs_input = await sidekick.run_superstep(user_msg, history)
    return history, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", None, new_sidekick


def free_resources(sidekick):
    try:
        if sidekick:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(sidekick.cleanup())
            except RuntimeError:
                asyncio.run(sidekick.cleanup())
    except Exception as e:
        print(f"Cleanup error: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    gr.Markdown("*Extended with clarifying questions, planning, and persistent memory.*")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=600, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="What can I help you with today?",
                scale=4,
            )
            go_button = gr.Button("Go!", variant="primary", scale=1)
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")

    ui.load(setup, [], [sidekick])
    message.submit(
        add_user_message, [message, chatbot], [message, chatbot]
    ).then(
        get_response, [sidekick, chatbot], [chatbot, sidekick]
    )
    go_button.click(
        add_user_message, [message, chatbot], [message, chatbot]
    ).then(
        get_response, [sidekick, chatbot], [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, chatbot, sidekick])


ui.launch(inbrowser=True)
