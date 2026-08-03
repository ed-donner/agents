#!/usr/bin/env python
"""Gradio chat UI: one coach question at a time, then LangGraph plan."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

from coach_graph import run_coach

QUESTIONS: list[str] = [
    "What is your weekly/monthly budget for food and activities?",
    "What city do you live in?",
    "How many hours a day do you spend in school?",
    "What is your height, weight, and gender?",
    "What subjects are you currently studying?",
    "What are your current grades in each of those subjects?"
]

def _opening_chat() -> list:
    return [[None, QUESTIONS[0]]]

def submit_answer(message: str, history: list, answers_so_far: list):
    history = list(history or [])
    answers_so_far = list(answers_so_far or [])

    if not (message and message.strip()):
        return history, answers_so_far, gr.update(value="")

    if len(answers_so_far) >= len(QUESTIONS):
        history.append(
            [
                message.strip(),
                "Intake is already complete. Click **Restart** to start a new plan.",
            ]
        )
        return history, answers_so_far, gr.update(value="")

    text = message.strip()
    new_answers = answers_so_far + [text]

    if len(new_answers) < len(QUESTIONS):
        bot = QUESTIONS[len(new_answers)]
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            bot = "Set `OPENAI_API_KEY` (repo-root `.env` or environment) to generate your plan."
            history.append([text, bot])
            return history, new_answers, gr.update(value="")

        transcript = "\n".join(
            f"{QUESTIONS[i]}\nAnswer: {new_answers[i]}" for i in range(len(QUESTIONS))
        )
        bot = run_coach(transcript)

    history.append([text, bot])
    return history, new_answers, gr.update(value="")

def restart():
    return _opening_chat(), [], gr.update(value="")

DESCRIPTION = """
The coach asks **one question at a time**. After your last answer, it runs the **LangGraph** pipeline for diet, exercise, study, and sleep plans.

**Educational only.**
"""

with gr.Blocks(theme=gr.themes.Default(primary_hue="cyan"), title="Student Lifestyle Coach") as demo:
    gr.Markdown(f"# Student Lifestyle Coach (LangGraph)\n{DESCRIPTION}")
    chat = gr.Chatbot(height=520, value=_opening_chat(), label="Coach")
    answers_state = gr.State([])
    msg = gr.Textbox(
        label="Your answer",
        placeholder="Type your answer, then Send",
        lines=2,
    )
    with gr.Row():
        send = gr.Button("Send", variant="primary")
        reset = gr.Button("Restart")

    send.click(submit_answer, [msg, chat, answers_state], [chat, answers_state, msg])
    msg.submit(submit_answer, [msg, chat, answers_state], [chat, answers_state, msg])
    reset.click(restart, outputs=[chat, answers_state, msg])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
