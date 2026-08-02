import gradio as gr

from sidekick import Sidekick


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    try:
        results, feedback = await sidekick.run_superstep(message, success_criteria, history)
        return results, feedback, sidekick
    except Exception as exc:
        error_text = f"Error: {exc}"
        print(error_text)
        return history + [{"role": "assistant", "content": error_text}], error_text, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, "", new_sidekick


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="Sidekick With Planner", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Sidekick With Planner (Week 4)")
    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=320, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(show_label=False, placeholder="Your request to the Sidekick")
        with gr.Row():
            success_criteria = gr.Textbox(show_label=False, placeholder="What are your success criteria?")

    with gr.Row():
        feedback = gr.Textbox(label="Evaluator Feedback", lines=3)

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, feedback, sidekick]
    )
    success_criteria.submit(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, feedback, sidekick]
    )
    go_button.click(
        process_message, [sidekick, message, success_criteria, chatbot], [chatbot, feedback, sidekick]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, feedback, sidekick])


ui.launch(inbrowser=True)
