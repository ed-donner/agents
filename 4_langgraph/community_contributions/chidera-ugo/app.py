import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Cleanup error: {e}")


with gr.Blocks(title="Chidera's Sidekick", theme=gr.themes.Default(primary_hue="blue")) as ui:
    gr.Markdown("## Chidera's Personal AI Sidekick")
    gr.Markdown(
        "Your AI co-worker. Browses the web, searches GitHub, writes and runs code, "
        "manages files, and remembers things across sessions."
    )

    sidekick_state = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=450, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="What do you need? (e.g. 'Research the best React state management options in 2025')",
                lines=2,
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria — what does done look like? (optional, leave blank for default)",
            )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick_state])
    message.submit(process_message, [sidekick_state, message, success_criteria, chatbot], [chatbot, sidekick_state])
    success_criteria.submit(process_message, [sidekick_state, message, success_criteria, chatbot], [chatbot, sidekick_state])
    go_button.click(process_message, [sidekick_state, message, success_criteria, chatbot], [chatbot, sidekick_state])
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick_state])


ui.launch(inbrowser=True)
