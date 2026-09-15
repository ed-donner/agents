from openai import OpenAI
from context import TWIN_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

openai = OpenAI()

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]


def chat(message, history):
    messages = list(system)

    for item in history:
        # Newer Gradio message format
        if isinstance(item, dict):
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })

        # Older Gradio tuple/list format
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_message, assistant_message = item

            if user_message:
                messages.append({
                    "role": "user",
                    "content": user_message
                })

            if assistant_message:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })

    messages.append({
        "role": "user",
        "content": message
    })

    response = openai.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        tools=tools
    )

    while response.choices[0].finish_reason == "tool_calls":
        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls
        results = handle_tool_calls(tool_calls)

        messages.append(assistant_message)
        messages.extend(results)

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools
        )

    return response.choices[0].message.content


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Max Hartvigsen | Digital Twin",
        description="Talk to my AI twin about my career, maritime experience, leadership background and marine technology.",
        chatbot=gr.Chatbot(
            show_label=False
        ),
    ).launch(
        css=CSS,
        js=JS,
        theme=gr.themes.Base()
    )