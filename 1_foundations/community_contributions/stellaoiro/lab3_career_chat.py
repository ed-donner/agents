"""
Week 1 Lab 3 — Career site chatbot with evaluator-rerun (Gradio).

Deploy to Hugging Face Spaces: Gradio SDK, set OPENAI_API_KEY in Space secrets.
Optionally set GOOGLE_API_KEY so the evaluator uses Gemini (same pattern as the course lab).
"""

from __future__ import annotations

import os
import socket
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv(override=True)

# HF Secrets / copy-pasted keys often end with \n — illegal inside Authorization headers
for _sek in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"):
    if os.environ.get(_sek) is not None:
        os.environ[_sek] = os.environ[_sek].strip()


def _env_secret(key: str) -> str:
    """Read env with .strip() for any key (defensive if set after load_dotenv)."""
    v = os.getenv(key)
    return (v or "").strip()


BASE = Path(__file__).resolve().parent
ME = BASE / "me"
PDF_PATH = ME / "linkedin.pdf"
SUMMARY_PATH = ME / "summary.txt"

NAME = _env_secret("CAREER_TWIN_NAME") or "Stella Oiro"
CHAT_MODEL = _env_secret("LAB3_CHAT_MODEL") or "gpt-4o-mini"

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
    gkey = _env_secret("GOOGLE_API_KEY") or _env_secret("GEMINI_API_KEY")
    if gkey:
        return (
            OpenAI(
                api_key=gkey,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            ),
            _env_secret("LAB3_EVAL_MODEL") or "gemini-2.5-flash",
        )
    return openai_client, _env_secret("LAB3_EVAL_MODEL") or "gpt-4o-mini"


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

# Dark violet / amethyst accent (no blue)
_PURPLE_PRIMARY = "#6D28D9"
_PURPLE_DEEP = "#5B21B6"
_PURPLE_HOVER = "#7C3AED"
_PURPLE_GLOW = "#A855F7"

_THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.purple,
    neutral_hue=gr.themes.colors.slate,
    font=gr.themes.GoogleFont("Inter"),
).set(
    body_background_fill="#0a0612",
    block_background_fill="#120b1c",
    block_border_color="rgba(139, 92, 246, 0.25)",
    body_text_color="#EDE9FE",
    block_label_text_color="#DDD6FE",
    button_primary_background_fill=_PURPLE_DEEP,
    button_primary_background_fill_hover=_PURPLE_HOVER,
    button_primary_text_color="#FAF5FF",
    slider_color=_PURPLE_GLOW,
    loader_color=_PURPLE_GLOW,
    input_background_fill="#1a1228",
    border_color_primary=_PURPLE_PRIMARY,
)

_CHAT_EXAMPLES = [
    "What's your background in healthcare technology?",
    "Tell me about your work at Evarest Technologies.",
    "What AI projects have you built?",
    "How did you transition from clinical medicine to software engineering?",
]

_ASSISTANT_AVATAR = (
    "https://api.dicebear.com/7.x/initials/svg?"
    "seed=SO&backgroundColor=5b21b6&textColor=fae8ff"
)

_description_lines = [
    f"**{NAME}** — Bridging clinical medicine and software: building AI that serves real people in health and technology.",
    "",
    "Every reply is **quality-checked by a second AI evaluator** before it is shown, so you get answers that stay on brief and on brand.",
    "",
    "- [LinkedIn](https://www.linkedin.com/in/stella-achar-oiro)",
    "- [GitHub](https://github.com/Stella-Achar-Oiro)",
]
if _missing_pdf:
    _description_lines.insert(
        0,
        "**Note:** `me/linkedin.pdf` was not found on disk; answers use `summary.txt` and stored context only.\n",
    )

_DESCRIPTION = "\n".join(_description_lines)

_CSS = """
.gradio-container {
    max-width: 820px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 1.35rem 1.1rem 2.25rem !important;
    background:
        radial-gradient(ellipse 120% 80% at 50% -20%, rgba(167, 139, 250, 0.18), transparent 55%),
        linear-gradient(180deg, #080510 0%, #0f0a18 45%, #0c0714 100%) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(139, 92, 246, 0.28) !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 28px 56px -18px rgba(76, 29, 149, 0.45) !important;
}
/* Shimmer / “glitter” primary actions */
.gradio-container button.primary,
.gradio-container .lg.primary {
    background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 42%, #6d28d9 78%, #5b21b6 100%) !important;
    border: 1px solid rgba(196, 181, 253, 0.45) !important;
    box-shadow:
        0 0 22px rgba(167, 139, 250, 0.35),
        0 4px 14px rgba(76, 29, 149, 0.4) !important;
    transition: filter 0.2s ease, box-shadow 0.2s ease !important;
}
.gradio-container button.primary:hover,
.gradio-container .lg.primary:hover {
    filter: brightness(1.08) saturate(1.05) !important;
    box-shadow:
        0 0 28px rgba(192, 132, 252, 0.5),
        0 6px 20px rgba(91, 33, 182, 0.45) !important;
}
.message-row .message, .message-wrap .message {
    box-shadow: 0 2px 14px rgba(88, 28, 135, 0.22) !important;
    border-radius: 14px !important;
    border: 1px solid rgba(167, 139, 250, 0.1) !important;
}
.gradio-chatbot h1, .chat-interface h1, .wrap > h1 {
    font-weight: 700 !important;
    font-size: 1.62rem !important;
    letter-spacing: -0.025em !important;
    background: linear-gradient(92deg, #f5f3ff 0%, #ddd6fe 40%, #c4b5fd 70%, #e9d5ff 100%) !important;
    -webkit-background-clip: text !important;
    background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    filter: drop-shadow(0 0 18px rgba(167, 139, 250, 0.35));
}
.gradio-container .prose, .gradio-container .prose p {
    color: #DDD6FE !important;
    line-height: 1.55 !important;
}
.gradio-container .prose a {
    color: #E9D5FF !important;
    font-weight: 500 !important;
    text-underline-offset: 3px !important;
}
.gradio-container .prose a:hover {
    color: #F5D0FE !important;
}
"""

with gr.Blocks(theme=_THEME, css=_CSS) as demo:
    _chatbot = gr.Chatbot(
        type="messages",
        avatar_images=(None, _ASSISTANT_AVATAR),
    )
    gr.ChatInterface(
        chat,
        type="messages",
        chatbot=_chatbot,
        title=f"Chat with {NAME}",
        description=_DESCRIPTION,
        examples=_CHAT_EXAMPLES,
        cache_examples=False,
    )


def pick_free_port(start: int, span: int = 40) -> int:
    """First TCP port in [start, start + span) we can bind to (avoids stale Gradio on 7860)."""
    for port in range(start, start + span):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise OSError(f"No free port in {start}-{start + span - 1}")


if __name__ == "__main__":
    _start = int(os.getenv("PORT", os.getenv("GRADIO_SERVER_PORT", "7860")))
    _port = pick_free_port(_start)
    print(f"Gradio using port {_port}", flush=True)
    demo.launch(server_name="0.0.0.0", server_port=_port)
