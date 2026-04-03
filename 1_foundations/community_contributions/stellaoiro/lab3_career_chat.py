"""
Week 1 Lab 3 — Career site chatbot with evaluator-rerun (Gradio).

Deploy to Hugging Face Spaces: Gradio SDK, set OPENAI_API_KEY in Space secrets.
Optionally set GOOGLE_API_KEY so the evaluator uses Gemini (same pattern as the course lab).
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv(override=True)

BASE = Path(__file__).resolve().parent
ME = BASE / "me"
PDF_PATH = ME / "linkedin.pdf"
SUMMARY_PATH = ME / "summary.txt"

NAME = os.getenv("CAREER_TWIN_NAME", "Stella Oiro")
CHAT_MODEL = os.getenv("LAB3_CHAT_MODEL", "gpt-4o-mini")

openai_client = OpenAI()


def _load_linkedin_text() -> str:
    if not PDF_PATH.is_file():
        return ""
    reader = PdfReader(str(PDF_PATH))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _load_summary() -> str:
    if not SUMMARY_PATH.is_file():
        return ""
    return SUMMARY_PATH.read_text(encoding="utf-8")


LINKEDIN = _load_linkedin_text()
SUMMARY = _load_summary()

system_prompt = (
    f"You are acting as {NAME}. You are answering questions on {NAME}'s website, "
    f"particularly questions related to {NAME}'s career, background, skills and experience. "
    f"Your responsibility is to represent {NAME} for interactions on the website as faithfully as possible. "
    f"You are given a summary of {NAME}'s background and LinkedIn profile which you can use to answer questions. "
    f"Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
    f"If you don't know the answer, say so.\n\n"
    f"## Summary:\n{SUMMARY}\n\n## LinkedIn Profile:\n{LINKEDIN}\n\n"
    f"With this context, please chat with the user, always staying in character as {NAME}."
)

evaluator_context = (
    f"## Summary:\n{SUMMARY}\n\n## LinkedIn Profile:\n{LINKEDIN}\n\n"
)


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def _evaluator_client_and_model() -> tuple[OpenAI, str]:
    gkey = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if gkey:
        return (
            OpenAI(
                api_key=gkey,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            os.getenv("LAB3_EVAL_MODEL", "gemini-2.5-flash"),
        )
    return openai_client, os.getenv("LAB3_EVAL_MODEL", "gpt-4o-mini")


evaluator_system_prompt = (
    f"You are an evaluator that decides whether a response to a question is acceptable. "
    f"You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. "
    f"The Agent is playing the role of {NAME} and is representing {NAME} on their website. "
    f"The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. "
    f"The Agent has been provided with context on {NAME}. Here's the information:\n\n"
    f"{evaluator_context}"
    f"With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
)


def evaluator_user_prompt(reply: str, message: str, history: list) -> str:
    user_prompt = f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


def evaluate(reply: str, message: str, history: list) -> Evaluation:
    ec, emodel = _evaluator_client_and_model()
    messages = [
        {"role": "system", "content": evaluator_system_prompt},
        {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
    ]
    response = ec.beta.chat.completions.parse(
        model=emodel,
        messages=messages,
        response_format=Evaluation,
    )
    parsed = response.choices[0].message.parsed
    assert parsed is not None
    return parsed


def rerun(reply: str, message: str, history: list, feedback: str) -> str:
    updated_system_prompt = (
        system_prompt
        + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        + f"## Your attempted answer:\n{reply}\n\n"
        + f"## Reason for rejection:\n{feedback}\n\n"
    )
    messages = (
        [{"role": "system", "content": updated_system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )
    response = openai_client.chat.completions.create(model=CHAT_MODEL, messages=messages)
    return response.choices[0].message.content or ""


def chat(message: str, history: list) -> str:
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": message}]
    response = openai_client.chat.completions.create(model=CHAT_MODEL, messages=messages)
    reply = response.choices[0].message.content or ""

    evaluation = evaluate(reply, message, history)
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply", flush=True)
    else:
        print("Failed evaluation - retrying", flush=True)
        print(evaluation.feedback, flush=True)
        reply = rerun(reply, message, history, evaluation.feedback)
    return reply


_missing_pdf = not PDF_PATH.is_file()
_desc_parts = [
    f"Week 1 Lab 3 — evaluator-rerun. Chatting as **{NAME}**.",
]
if _missing_pdf:
    _desc_parts.insert(
        0,
        "**Note:** `me/linkedin.pdf` was not found; answers use `summary.txt` only.",
    )

demo = gr.ChatInterface(
    chat,
    type="messages",
    title=f"Chat with {NAME}",
    description="\n\n".join(_desc_parts),
)

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
