import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

from agent import run_agent

def chat(user_input, history):
    result = run_agent(user_input)
    return str(result)

with gr.Blocks() as demo:
    gr.Markdown("# 📧 Gmail MCP AI Assistant")

    chatbot = gr.ChatInterface(
        fn=chat,
        type="messages",
        title="Talk to your Gmail",
    )

demo.launch()