from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env", override=True)

from graph import run_bartender

QUESTIONS = [
    "What spirits do you have? Vodka, rum, whiskey, gin, tequila, anything else?",
    "Any mixers? Tonic, soda, juices, simple syrup, bitters?",
    "Fresh stuff? Limes, lemons, mint, berries, cucumber, anything like that?",
    "Bar tools? Shaker, muddler, jigger — or just winging it with glasses?",
    "What are you in the mood for? Strong, sweet, sour, fruity, classic, surprise me?",
]


def _opening():
    return [[None, QUESTIONS[0]]]


def on_send(msg, history, answers):
    history = list(history or [])
    answers = list(answers or [])

    if not msg or not msg.strip():
        return history, answers, gr.update(value="")

    if len(answers) >= len(QUESTIONS):
        history.append([msg.strip(), "Already got everything. Hit **Restart** to go again."])
        return history, answers, gr.update(value="")

    answers = answers + [msg.strip()]

    if len(answers) < len(QUESTIONS):
        reply = QUESTIONS[len(answers)]
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            reply = "Need `OPENAI_API_KEY` to do anything useful. Check your `.env`."
            history.append([msg.strip(), reply])
            return history, answers, gr.update(value="")

        transcript = "\n".join(
            f"{QUESTIONS[i]}\n{answers[i]}" for i in range(len(QUESTIONS))
        )
        reply = run_bartender(transcript)

    history.append([msg.strip(), reply])
    return history, answers, gr.update(value="")


def restart():
    return _opening(), [], gr.update(value="")


with gr.Blocks(
    theme=gr.themes.Default(primary_hue="amber"),
    title="Home Bartender",
) as demo:
    gr.Markdown(
        "# Home Bartender\n"
        "Tell me what you've got and I'll figure out what you can make tonight."
    )
    chat = gr.Chatbot(height=480, value=_opening(), label="Bartender")
    answers_state = gr.State([])
    msg = gr.Textbox(label="Your answer", placeholder="Type here...", lines=2)
    with gr.Row():
        send = gr.Button("Send", variant="primary")
        reset = gr.Button("Restart")

    send.click(on_send, [msg, chat, answers_state], [chat, answers_state, msg])
    msg.submit(on_send, [msg, chat, answers_state], [chat, answers_state, msg])
    reset.click(restart, outputs=[chat, answers_state, msg])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
