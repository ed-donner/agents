import gradio as gr
from sidekick import Sidekick, TONE_OPTIONS, DEFAULT_TONE


async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, tone, history):
    results = await sidekick.run_superstep(message, success_criteria, tone, history)
    return results, sidekick


async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", None, None, new_sidekick


def free_resources(sidekick):
    print("Cleaning up browser resources...")
    try:
        if sidekick:
            sidekick.cleanup()
    except Exception as e:
        print(f"Cleanup error: {e}")


tone_choices = list(TONE_OPTIONS.keys())

with gr.Blocks(
    title="Content Creator Sidekick",
    theme=gr.themes.Default(primary_hue="purple")
) as ui:

    gr.Markdown("## Content Creator Sidekick")
    gr.Markdown("Write viral content for any platform. Research, draft, check limits, save — all in one loop.")

    sidekick = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="Sidekick", height=400, type="messages")

    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder="What content do you want? e.g. 'Write a LinkedIn post about AI agents' or 'Write a YouTube script about Python tips'",
                lines=2,
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder="Success criteria — e.g. 'Must include 5 hashtags, under 280 chars, saved to file'",
            )
        with gr.Row():
            tone = gr.Dropdown(
                choices=tone_choices,
                value=DEFAULT_TONE,
                label="Tone / Voice",
                interactive=True,
            )

    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Create!", variant="primary")

    ui.load(setup, [], [sidekick])

    message.submit(
        process_message,
        [sidekick, message, success_criteria, tone, chatbot],
        [chatbot, sidekick],
    )
    success_criteria.submit(
        process_message,
        [sidekick, message, success_criteria, tone, chatbot],
        [chatbot, sidekick],
    )
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, tone, chatbot],
        [chatbot, sidekick],
    )
    reset_button.click(
        reset, [], [message, success_criteria, chatbot, tone, sidekick]
    )


ui.launch(inbrowser=True)
