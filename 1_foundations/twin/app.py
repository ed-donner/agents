import os

from openai import OpenAI
from context import TWIN_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

MODEL_NAME = os.getenv('GOOGLE_SMALL_MODEL')
API_KEY = os.getenv('GEMINI_API_KEY')
BASE_URL = os.getenv('GOOGLE_API_BASE_URL')


openai = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]


def chat(message, history):
    messages = system + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
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
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 10000)),
    css=CSS,
    js=JS,
    theme=gr.themes.Base(),
)