import gradio as gr
from outreach_sidekick import OutreachSidekick


async def setup():
    sidekick = OutreachSidekick()
    await sidekick.setup()
    return sidekick


async def process_message(sidekick, message, success_criteria, history):
    if not sidekick:
        sidekick = await setup()
    results = await sidekick.run_superstep(message, success_criteria, history)
    return results, sidekick


async def reset():
    new_sidekick = OutreachSidekick()
    await new_sidekick.setup()
    return "", "", None, new_sidekick


with gr.Blocks(
    title="Outreach Sidekick",
    theme=gr.themes.Default(primary_hue="blue", secondary_hue="emerald"),
) as ui:
    gr.Markdown("## Outreach Sidekick — Research-Backed Cold Email Agent")
    gr.Markdown(
        "*Researches your prospect, drafts multiple variants, evaluates "
        "quality, and saves the winning email — with built-in policy "
        "guardrails.*"
    )

    sidekick = gr.State()

    with gr.Row():
        chatbot = gr.Chatbot(
            label="Outreach Sidekick", height=400, type="messages"
        )
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False,
                placeholder=(
                    "Describe your outreach target and offer "
                    "(e.g. 'Email the VP Eng at Stripe about our CI/CD tool')"
                ),
                lines=2,
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False,
                placeholder=(
                    "Success criteria "
                    "(e.g. 'Under 100 words, mention their Series C, "
                    "suggest a 15-min call')"
                ),
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Generate Outreach", variant="primary")

    ui.load(setup, [], [sidekick])
    message.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick],
    )
    success_criteria.submit(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick],
    )
    go_button.click(
        process_message,
        [sidekick, message, success_criteria, chatbot],
        [chatbot, sidekick],
    )
    reset_button.click(
        reset, [], [message, success_criteria, chatbot, sidekick]
    )


ui.launch(inbrowser=True)
