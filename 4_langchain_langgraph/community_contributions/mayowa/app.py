import gradio as gr

from sidekick import MedicalSidekick


async def setup():
    sidekick = MedicalSidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, care_goal, history):
    results = await sidekick.run_superstep(message, care_goal, history)
    return results, sidekick, ""


async def reset():
    new_sidekick = MedicalSidekick()
    await new_sidekick.setup()
    return "", "", [], new_sidekick


def free_resources(sidekick):
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as exc:
        print(f"Cleanup error: {exc}")


with gr.Blocks(
    title="Mayowa Medical Sidekick",
    theme=gr.themes.Default(primary_hue="blue"),
) as ui:
    gr.Markdown(
        """
        ## Mayowa Medical Sidekick
        Ask a medical question and the assistant will start with clarifying questions before giving guidance.

        This app is for general medical information only and is not a substitute for a clinician or emergency care.
        """
    )
    sidekick = gr.State(delete_callback=free_resources)

    chatbot = gr.Chatbot(label="Medical Sidekick", height=420, type="messages")

    with gr.Group():
        message = gr.Textbox(
            show_label=False,
            placeholder="Describe the symptom, concern, or medical question",
        )
        care_goal = gr.Textbox(
            show_label=False,
            placeholder="Optional: what would make the answer most helpful for you?",
        )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Ask", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message,
        [sidekick, message, care_goal, chatbot],
        [chatbot, sidekick, message],
    )
    care_goal.submit(
        process_message,
        [sidekick, message, care_goal, chatbot],
        [chatbot, sidekick, message],
    )
    go_button.click(
        process_message,
        [sidekick, message, care_goal, chatbot],
        [chatbot, sidekick, message],
    )
    reset_button.click(reset, [], [message, care_goal, chatbot, sidekick])


ui.launch(inbrowser=True)
