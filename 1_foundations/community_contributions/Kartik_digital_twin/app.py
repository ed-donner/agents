from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)
from context import TWIN_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
import gradio as gr
import os

# load_dotenv(override=True)

MODEL_NAME = "openai/gpt-oss-120b"

Groq = os.getenv("GROQ_API_KEY")
Groq_url = os.getenv("GROQ_BASE_URL")

openai = OpenAI(api_key=Groq, base_url=Groq_url)

system = [{"role":"system", "content": TWIN_SYSTEM_PROMPT}]


def chat(message, history):
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = system + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    return response.choices[0].message.content

if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title='''Kartik Jakhar's Digital Twin''',
        description="Feel free to ask anything about me. This is very close",
        chatbot=gr.Chatbot(show_label=False)
    ).launch(css=CSS,js=JS,theme=gr.themes.Base(),inbrowser=True)