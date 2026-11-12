from openai import OpenAI
from context import TRIP_PLANNER_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr
import os

load_dotenv(override=True)

azure_api_key = os.getenv("AZURE_API_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")

deployment_name_gpt_5_mini = "gpt-5-mini"
deployment_name_gpt_4_1_nano = "gpt-4.1-nano"

openai = OpenAI(api_key=azure_api_key, base_url=endpoint)

system_prompt = [{"role": "system", "content": TRIP_PLANNER_SYSTEM_PROMPT}]

def chat(message, history):
    messages = system_prompt + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=deployment_name_gpt_5_mini, messages=messages, tools=tools)
    while response.choices[0].finish_reason=="tool_calls":
        message = response.choices[0].message
        tool_calls = message.tool_calls
        results = handle_tool_calls(tool_calls)
        messages.append(message)
        messages.extend(results)
        response = openai.chat.completions.create(model=deployment_name_gpt_5_mini, messages=messages, tools=tools)
    return response.choices[0].message.content

WELCOME_MESSAGE = f"""
    Hi! I'm Jowie, your trip planning assistant. I can help you plan your trip.

    To get started, please share your name, destination, number of travelers, and number of days.
    You can also include your email (optional) and any useful details, such as your budget, interests, travel dates, or accessibility needs.
"""

chatbot = gr.Chatbot(value=[{"role": "assistant", "content": WELCOME_MESSAGE}], show_label=False)

gr.ChatInterface(fn=chat, chatbot=chatbot).launch(inbrowser=True)

if __name__ == "__main__":
    gr.ChatInterface(
        fn=chat,
        examples=EXAMPLES,
        title="Trip Planner",
        description="Plan your perfect trip with Jowie!",
        chatbot=chatbot,
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())
