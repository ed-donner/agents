import gradio as gr
from agent import Agent

agent = Agent()


def chat(message, history):
    return agent.chat(message, history)


if __name__ == "__main__":
    gr.ChatInterface(chat, type="messages").launch()
