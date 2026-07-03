import gradio as gr
from advisor import FarmAdvisor


WELCOME_MESSAGE = (
    "Hey there! I'm FarmAdvisor, your AI-powered agricultural input assistant. "
    "Tell me about your farm -- what crop are you growing, where are you located, "
    "and what problem or challenge are you dealing with? "
    "I'll research the best fertilisers, seeds, and pesticides for your situation "
    "and send you a full advisory report."
)

# Quick-load examples

EXAMPLES = [
    "I'm growing maize in Kano, Nigeria. The plants are about 4 weeks old and the leaves are turning yellow from the bottom up. Growth looks stunted.",
    "I have a tomato farm in Ibadan. I'm seeing small holes in the leaves and some fruits are rotting on the vine. What pesticides should I use?",
    "I want to start planting rice in Lagos state. It's my first time. What seeds and fertilisers should I use to get a good yield?",
]

# Gradio app

async def chat(message: str, history: list, advisor: FarmAdvisor):
    if advisor is None:
        advisor = FarmAdvisor()
        await advisor.setup()

    try:
        updated_history = await advisor.run(message=message, history=history)
        return updated_history, advisor
    except Exception as e:
        import traceback
        error_msg = f"Something went wrong: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        return history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": error_msg}
        ], advisor


async def setup_advisor():
    advisor = FarmAdvisor()
    await advisor.setup()
    return advisor


async def reset_advisor():
    advisor = FarmAdvisor()
    await advisor.setup()
    return [], advisor


with gr.Blocks(title="FarmAdvisor", theme=gr.themes.Default(primary_hue="green")) as demo:

    gr.Markdown("# 🌱 FarmAdvisor Sidekick")
    gr.Markdown(
        "AI-powered farm input advisory -- fertilisers, seeds, and pesticides "
        "grounded in live web research, Wikipedia, and real-time weather data."
    )

    advisor_state = gr.State()

    chatbot = gr.Chatbot(
        value=[{"role": "assistant", "content": WELCOME_MESSAGE}],
        type="messages",
        height=520,
        label="FarmAdvisor",
        show_label=False,
    )

    with gr.Row():
        msg_box = gr.Textbox(
            show_label=False,
            placeholder="Describe your crop, location, and problem...",
            scale=8
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    with gr.Row():
        reset_btn = gr.Button("Start new conversation", variant="stop", scale=1)

    with gr.Accordion("Quick-load examples", open=True):
        with gr.Row():
            ex1_btn = gr.Button("🌽 Maize yellowing -- Kano", variant="secondary")
            ex2_btn = gr.Button("🍅 Tomato pest -- Ibadan", variant="secondary")
            ex3_btn = gr.Button("🌾 Rice planting -- Lagos", variant="secondary")


    async def handle_message(message, history, advisor):
        if not message or not message.strip():
            return history, "", advisor
        updated_history, updated_advisor = await chat(message, history, advisor)
        return updated_history, "", updated_advisor

    send_btn.click(
        fn=handle_message,
        inputs=[msg_box, chatbot, advisor_state],
        outputs=[chatbot, msg_box, advisor_state]
    )

    msg_box.submit(
        fn=handle_message,
        inputs=[msg_box, chatbot, advisor_state],
        outputs=[chatbot, msg_box, advisor_state]
    )

    reset_btn.click(
        fn=reset_advisor,
        outputs=[chatbot, advisor_state]
    )

    # Quick-load buttons populate the message box
    ex1_btn.click(fn=lambda: EXAMPLES[0], outputs=msg_box)
    ex2_btn.click(fn=lambda: EXAMPLES[1], outputs=msg_box)
    ex3_btn.click(fn=lambda: EXAMPLES[2], outputs=msg_box)

    # Initialise advisor on load
    demo.load(fn=setup_advisor, outputs=advisor_state)


if __name__ == "__main__":
    demo.launch(inbrowser=True)