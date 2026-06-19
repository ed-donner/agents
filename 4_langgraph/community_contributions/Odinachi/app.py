import gradio as gr
from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    try:
        await sidekick.setup()
    except Exception as e:
        print(f"Sidekick setup failed: {e}")
        raise
    return sidekick


def _not_ready_reply(message: str) -> list:
    text = (
        "Sidekick did not finish starting (see terminal). "
        "If the error mentioned Playwright, run: `uv run playwright install chromium`"
    )
    return [
        {"role": "user", "content": message},
        {"role": "assistant", "content": text},
    ]


async def process_message(sidekick, message, success_criteria, history):
    if sidekick is None or getattr(sidekick, "graph", None) is None:
        return (history or []) + _not_ready_reply(message or ""), sidekick
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    new_sidekick = Sidekick()
    try:
        await new_sidekick.setup()
    except Exception as e:
        print(f"Sidekick reset/setup failed: {e}")
        raise
    return "", "", None, new_sidekick


def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick Pro", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick with planning")
    gr.Markdown(
        "Each run: **planner** builds ordered steps, then the **worker** executes with tools and the **evaluator** checks success criteria."
    )
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=300, type="messages")
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, placeholder="What are your success criteria?"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, sidekick]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, sidekick])


ui.launch(inbrowser=True)
