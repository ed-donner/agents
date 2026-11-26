from openai import OpenAI
from context import TWIN_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from evaluator import evaluate
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

MODEL_NAME = "gpt-5.4-mini"

openai = OpenAI()


def run_twin(messages):
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        msg = response.choices[0].message
        messages.append(msg)
        messages.extend(handle_tool_calls(msg.tool_calls))
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    return response.choices[0].message.content


def rerun(reply, message, history, feedback):
    updated_prompt = TWIN_SYSTEM_PROMPT + f"""

## Previous answer rejected
Your attempted answer:
{reply}

Reason for rejection:
{feedback}

Write a completely new answer in plain, professional English.
"""
    messages = [{"role": "system", "content": updated_prompt}] + history + [{"role": "user", "content": message}]
    return run_twin(messages)


def chat(message, history):
    messages = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]
    reply = run_twin(messages)

    evaluation = evaluate(reply, message, history)
    if evaluation.is_acceptable:
        print("Passed evaluation", flush=True)
    else:
        print(f"Failed evaluation: {evaluation.feedback}", flush=True)
        reply = rerun(reply, message, history, evaluation.feedback)
    return reply


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())