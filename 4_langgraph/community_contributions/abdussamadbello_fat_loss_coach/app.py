#!/usr/bin/env python
"""Gradio chat UI: one coach question at a time, then LangGraph plan."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

# Repo root is three levels above this file (…/4_langgraph/community_contributions/this_folder/).
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

from coach_graph import run_coach

# Intake order: one question per user message before the graph runs.
QUESTIONS: list[str] = [
    "What is your main goal (fat loss, recomposition, or health markers you care about)?",
    "Rough weekly food budget in USD (or say “flexible” / “not sure”).",
    "Monthly gym or equipment budget (USD), or say “home only” / “walking only”.",
    "How many minutes per day can you realistically spend on training and meal prep?",
    "Diet preferences, allergies, or foods you avoid (cultural, ethical, taste)?",
    "Any injuries, pain, or doctor limits I should respect for training?",
]


def _opening_chat() -> list:
    """First turn: assistant asks question 1; user message is None."""
    return [[None, QUESTIONS[0]]]


def submit_answer(message: str, history: list, answers_so_far: list):
    """Append user reply; reply with next question or final plan."""
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
The coach asks **one question at a time**. After your last answer, it runs the **LangGraph** pipeline (parse → training → nutrition → budget → full plan).

**Educational only—not medical advice.**
"""


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Fat loss coach") as demo:
    gr.Markdown(f"# Fat loss coach (LangGraph)\n{DESCRIPTION}")
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
