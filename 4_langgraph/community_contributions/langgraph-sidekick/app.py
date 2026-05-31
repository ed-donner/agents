from dotenv import load_dotenv
load_dotenv(override=True)
import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick

async def process_message(sidekick, message, history):
    history, _ = await sidekick.run_superstep(message, history)
    return history, sidekick

async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", None, new_sidekick

async def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            await sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick Personal Co-Worker")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(value=[], label="Sidekick", height=300)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message,
        [sidekick, message, chatbot],
        [chatbot, sidekick]
    )
    go_button.click(
        process_message,
        [sidekick, message, chatbot],
        [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, chatbot, sidekick])


ui.launch(inbrowser=True)
