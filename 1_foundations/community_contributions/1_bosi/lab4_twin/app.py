"""Digital twin with an evaluator guardrail. Run from the repo root: uv run 1_foundations/community_contributions/1_bosi/lab4_twin/app.py
Needs OPENAI_API_KEY and ANTHROPIC_API_KEY in .env; PUSHOVER_USER and PUSHOVER_TOKEN for notifications."""

from dotenv import load_dotenv

load_dotenv(override=True)

import gradio as gr
from openai import OpenAI

from context import NAME, TWIN_SYSTEM_PROMPT
from evaluator import evaluate, text_of
from styles import CSS, JS, EXAMPLES, THEME, greeting
from tools import tools, handle_tool_calls

MODEL_NAME = "gpt-5.4-mini"

openai = OpenAI()

MAX_ATTEMPTS = 3
FALLBACK_REPLY = (
    "I'd rather keep our chat focused on my professional background. "
    "Feel free to ask about my experience, skills or projects, or leave your email if you'd like to get in touch!"
)


def run_agent(messages, use_tools=True):
    """Call the LLM, running any tools it asks for, until it gives a final reply."""
    extra = {"tools": tools} if use_tools else {}
    response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, **extra)
    while response.choices[0].finish_reason == "tool_calls":
        message = response.choices[0].message
        messages.append(message)
        messages.extend(handle_tool_calls(message.tool_calls))
        response = openai.chat.completions.create(model=MODEL_NAME, messages=messages, **extra)
    return response.choices[0].message.content


def chat(message, history):
    # Keep only role and content: Gradio can add extra keys (like metadata) that the API rejects
    history = [{"role": h["role"], "content": text_of(h["content"])} for h in history]
    prompt = TWIN_SYSTEM_PROMPT

    for attempt in range(1, MAX_ATTEMPTS + 1):
        messages = [{"role": "system", "content": prompt}] + history + [{"role": "user", "content": message}]
        # Tools only run on the first attempt, so retries don't send duplicate notifications
        reply = run_agent(messages, use_tools=(attempt == 1))

        try:
            evaluation = evaluate(reply, message, history)
        except Exception as e:
            # If the checker itself fails, don't block the visitor: show the reply and log the problem
            print(f"[Evaluator] Error, showing reply unchecked: {e}", flush=True)
            return reply

        verdict = "PASSED" if evaluation.is_acceptable else "REJECTED"
        print(f"[Evaluator] Attempt {attempt} {verdict}: {evaluation.feedback}", flush=True)
        if evaluation.is_acceptable:
            return reply

        prompt = TWIN_SYSTEM_PROMPT + f"""

# Your previous answer was rejected

A quality checker rejected your last reply because it did not stay on professional topics.

Your rejected reply:
{reply}

Reason:
{evaluation.feedback}

Write a new reply that stays on professional topics.
"""

    return FALLBACK_REPLY


if __name__ == "__main__":
    gr.ChatInterface(
        chat,
        examples=EXAMPLES,
        title=NAME,
        chatbot=gr.Chatbot(show_label=False, placeholder=greeting(NAME)),
        textbox=gr.Textbox(placeholder="Ask about my experience…", show_label=False, submit_btn=True),
    ).launch(css=CSS, js=JS, theme=THEME)
