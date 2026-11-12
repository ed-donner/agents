import gradio as gr
from app import chat

if __name__ == "__main__":
    gr.ChatInterface(chat).launch(inbrowser=True)
