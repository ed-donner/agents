import os
import gradio as gr
from agent import run_date_agent


def build_ui():
    with gr.Blocks() as ui:
        gr.Markdown("## MCP Date Assistant  (Gradio -> Agents SDK -> MCP stdio server)")

        with gr.Row():
            with gr.Column(scale=3):
                chat = gr.Chatbot(type='messages', label="Date Assistant", height=520)
                txt = gr.Textbox(
                    show_label=False,
                    placeholder="Ask about dates or time (press Enter)",
                )
                with gr.Row():
                    submit = gr.Button("Send", variant="primary")
                    clear = gr.Button("Clear")

        state = gr.State([])

        async def respond(message, chat_history):
            if not message or not message.strip():
                return "", chat_history

            chat_history.append({"role": "user", "content": message})

            try:
                agent_reply = await run_date_agent(message)
                if isinstance(agent_reply, dict):
                    agent_reply = agent_reply.get("output", str(agent_reply))
                chat_history.append({"role": "assistant", "content": str(agent_reply)})
            except Exception as e:
                chat_history.append({"role": "assistant", "content": f"Agent error: {e}"})

            return "", chat_history

        txt.submit(respond, [txt, state], [txt, chat])
        submit.click(respond, [txt, state], [txt, chat])
        clear.click(lambda: ([], ""), outputs=[chat, txt])

    return ui


if __name__ == "__main__":
    app = build_ui()
    app.launch(server_name="0.0.0.0", server_port=7861, share=False)
