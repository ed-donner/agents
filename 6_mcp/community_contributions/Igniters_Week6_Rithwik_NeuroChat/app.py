import gradio as gr
from agent import run_agent_streamed


async def chat(user_message: str, history: list):
    if not user_message.strip():
        return

    # Convert Gradio [user, assistant] pairs -> SDK {role, content} dicts
    sdk_history: list[dict] = []
    for user_msg, assistant_msg in history:
        sdk_history.append({"role": "user", "content": user_msg})
        if assistant_msg:
            sdk_history.append({"role": "assistant", "content": assistant_msg})

    # Show user message immediately with a placeholder
    history = history + [[user_message, "⏳ Thinking..."]]
    yield history, history, ""

    # creates a placeholder for the answer and updates it as the agent works
    async for status, answer in run_agent_streamed(user_message, sdk_history):
        if status:
            history[-1][1] = f"⏳ {status}"
            yield history, history, ""
        if answer:
            history[-1][1] = answer
            yield history, history, ""


with gr.Blocks(title="NeuroChat", theme=gr.themes.Default()) as demo:

    gr.Markdown("# 🧠 NeuroChat")
    gr.Markdown("Ask anything about neuroscience. Type a question and press **Enter** or click **Send**.")

    chatbot = gr.Chatbot(height=450, show_copy_button=True, label="")

    with gr.Row():
        msg = gr.Textbox(
            placeholder="e.g. What is the hippocampus?",
            label="Your question",
            scale=8,
            autofocus=True,
        )
        send_btn = gr.Button("Send", scale=1, variant="primary")

    clear_btn = gr.Button("Clear chat")

    gr.Examples(
        label="Try one of these:",
        examples=[
            "What is the hippocampus?",
            "Explain neuroplasticity in simple terms",
            "Recent research on BDNF and depression",
            "What does the literature say about adult neurogenesis?",
            "How does the blood-brain barrier work?",
        ],
        inputs=msg,
    )

    state = gr.State([])

    msg.submit(chat, [msg, state], [chatbot, state, msg])
    send_btn.click(chat, [msg, state], [chatbot, state, msg])
    clear_btn.click(lambda: ([], [], ""), outputs=[chatbot, state, msg])


if __name__ == "__main__":
    demo.launch(inbrowser=True)