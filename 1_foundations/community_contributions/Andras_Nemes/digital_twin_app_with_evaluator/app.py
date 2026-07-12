import os
import warnings

from openai import OpenAI
from pydantic import BaseModel
from context import TWIN_SYSTEM_PROMPT, EVALUATOR_SYSTEM_PROMPT
from tools import tools, handle_tool_calls
from styles import CSS, JS, EXAMPLES
from dotenv import load_dotenv
import gradio as gr

load_dotenv(override=True)

# Silence a deprecation warning that Gradio triggers inside Starlette; not caused by this app.
warnings.filterwarnings("ignore", message=".*HTTP_422_UNPROCESSABLE_ENTITY.*")

MODEL_NAME = "gpt-5.4-mini"
EVALUATOR_MODEL_NAME = "gemini-2.5-flash"

openai = OpenAI()
gemini = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

system = [{"role": "system", "content": TWIN_SYSTEM_PROMPT}]


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def run_with_tools(message, history):
    messages = system + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    while response.choices[0].finish_reason == "tool_calls":
        tool_message = response.choices[0].message
        results = handle_tool_calls(tool_message.tool_calls)
        messages.append(tool_message)
        messages.extend(results)
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, tools=tools)
    return response.choices[0].message.content


def evaluate(reply, message, history):
    user_prompt = f"Here's the conversation between the User and the Agent:\n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User:\n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent:\n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    messages = [
        {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = gemini.beta.chat.completions.parse(
        model=EVALUATOR_MODEL_NAME, messages=messages, response_format=Evaluation
    )
    return response.choices[0].message.parsed


def rerun(reply, message, history, feedback):
    updated_system_prompt = TWIN_SYSTEM_PROMPT + f"""

## Previous reply rejected

You just tried to reply, but the quality control rejected your reply.

## Your attempted reply:

{reply}

## Reason for rejection:

{feedback}

Please reply again. Do not mention the evaluation process.
"""
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    # The retry deliberately gets no tools, so notifications don't fire twice for one reply.
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages)
    return response.choices[0].message.content


def chat(message, history):
    reply = run_with_tools(message, history)
    evaluation = evaluate(reply, message, history)
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply", flush=True)
        return reply
    print(f"Failed evaluation - retrying. Feedback: {evaluation.feedback}", flush=True)
    return rerun(reply, message, history, evaluation.feedback)


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title="Digital Twin",
        description="Talk to my AI twin about my career",
        chatbot=gr.Chatbot(show_label=False),
    ).launch(css=CSS, js=JS, theme=gr.themes.Base())
