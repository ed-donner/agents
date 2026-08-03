from __future__ import annotations

import logging
import os
import socket
import uuid
from typing import List, Optional

import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage

from education_coach.config import bootstrap_env, get_settings
from education_coach.email_delivery import (
    email_ready,
    is_valid_recipient,
    send_conversation_to_student,
)
from education_coach.graph import build_app_graph
from education_coach.guardrails import input_guardrail_stub, output_guardrail_stub

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CRITERIA = (
    "Be a supportive tutor: learn what the student is studying (subject or course topic) and their level "
    "(e.g. grade, year, or beginner/intermediate/advanced) before long explanations. If either is missing or vague, "
    "ask short, specific questions first—then teach at the right depth, use tools when facts need verification, "
    "and end with a quick check-for-understanding or suggested next step."
)

MISSING_KEY_MARKDOWN = (
    "This coach can’t respond yet because it isn’t fully configured. "
    "If you’re visiting a shared link, contact whoever published it."
)

INIT_ERROR_USER = "The coach couldn’t start. Please try again in a moment."


def _friendly_chat_error(exc: BaseException) -> str:
    name = type(exc).__name__
    msg = (str(exc) or "").strip()[:320]
    combined = f"{name} {msg}".lower()
    if "ratelimit" in name.lower() or "429" in msg or "rate_limit" in combined:
        return "Rate limited — wait a moment and try again."
    if "apiconnection" in name.lower() or "connecterror" in combined or "connection error" in combined:
        return "Network error — check connectivity and try again."
    if (
        "authentication" in name.lower()
        or "401" in msg
        or "invalid_api_key" in combined
        or "incorrect api key" in combined
    ):
        return "API authentication failed — check OPENAI_API_KEY."
    if "timeout" in combined:
        return "Request timed out — try a shorter question or retry."
    return f"Something went wrong ({name}). Please try again."


def _latest_tutor_preview(msgs) -> str:
    for m in reversed(msgs or []):
        if not isinstance(m, AIMessage):
            continue
        c = (m.content or "").strip()
        if c.startswith("Evaluator:"):
            continue
        tool_calls = getattr(m, "tool_calls", None) or []
        if tool_calls and not c:
            return "Using Wikipedia / web search…"
        if c:
            return c
    return ""


def _streaming_chat_messages(history: List, user_msg: dict, msgs) -> List:
    tutor = _latest_tutor_preview(msgs)
    out: List = list(history) + [user_msg]
    out.append({"role": "assistant", "content": tutor or "…"})
    return out


def _extract_tutor_and_eval_text(msgs):
    if not msgs:
        return "", ""
    eval_text = getattr(msgs[-1], "content", "") or ""
    tutor_text = ""
    for m in reversed(msgs[:-1]):
        if not isinstance(m, AIMessage):
            continue
        content = (m.content or "").strip()
        if not content or content.startswith("Evaluator:"):
            continue
        tutor_text = content
        break
    return tutor_text, eval_text


def _try_send_history_email(student_email: str, new_history: List) -> str:
    if not (student_email or "").strip():
        return ""
    if not is_valid_recipient(student_email):
        return "Email not sent: invalid address."
    if not email_ready():
        return "Email isn’t available on this setup right now."
    try:
        send_conversation_to_student(to_email=student_email.strip(), history=new_history)
        return f"Sent copy to {student_email.strip()}."
    except Exception as e:
        logger.exception("Email send failed")
        brief = (str(e) or type(e).__name__).strip()[:400]
        if len(str(e)) > 400:
            brief += "…"
        return f"Email failed: {brief}"


def create_demo():
    bootstrap_env()
    settings = get_settings()
    graph = None
    banner: Optional[str] = None

    if settings.openai_api_key:
        os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)

    if not settings.openai_api_key:
        banner = MISSING_KEY_MARKDOWN
    else:
        try:
            graph, _ = build_app_graph()
        except Exception:
            logger.exception("Failed to build agent graph")
            banner = INIT_ERROR_USER

    def make_thread_id() -> str:
        return str(uuid.uuid4())

    def _email_offer_hidden():
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    def _email_offer_show():
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    async def process_message(
        message: str,
        history: List,
        thread: str,
    ):
        hid = _email_offer_hidden()
        if not (message or "").strip():
            yield history, thread, "", *hid
            return

        user = {"role": "user", "content": message.strip()}
        guard = input_guardrail_stub(message)
        if guard:
            yield history + [user, {"role": "assistant", "content": guard}], thread, "", *hid
            return

        if graph is None:
            note = banner or "The coach isn’t available right now."
            yield history + [user, {"role": "assistant", "content": note}], thread, "", *hid
            return

        try:
            criteria = DEFAULT_CRITERIA
            config = {"configurable": {"thread_id": thread}}
            state = {
                "messages": [HumanMessage(content=message.strip())],
                "success_criteria": criteria,
                "feedback_on_work": None,
                "success_criteria_met": False,
                "user_input_needed": False,
                "evaluator_iterations": 0,
            }
            last_values: dict | None = None
            async for values in graph.astream(state, config, stream_mode="values"):
                last_values = values
                msgs = values.get("messages", [])
                preview = _streaming_chat_messages(history, user, msgs)
                yield preview, thread, "", *hid

            if last_values is None:
                yield history + [
                    user,
                    {"role": "assistant", "content": "No response this time. Try again."},
                ], thread, "", *hid
                return

            msgs = last_values["messages"]
            tutor_text, _ = _extract_tutor_and_eval_text(msgs)
            policy = output_guardrail_stub(tutor_text or "")
            if policy:
                tutor_text = f"[Response withheld: {policy}]"
            reply = {"role": "assistant", "content": tutor_text or "(no tutor text)"}
            new_history = history + [user, reply]
            show = _email_offer_show()
            yield new_history, thread, "", *show
        except Exception as e:
            logger.exception("Chat turn failed")
            yield history + [
                user,
                {"role": "assistant", "content": _friendly_chat_error(e)},
            ], thread, "", *hid

    def on_email_no():
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    def on_email_yes():
        return (
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def on_email_send(history: List, addr: str):
        if not history:
            msg = "There’s nothing to send yet."
        else:
            msg = _try_send_history_email(addr, list(history))
        return (
            msg,
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(value=""),
        )

    async def reset():
        hid = _email_offer_hidden()
        return "", None, make_thread_id(), "", *hid, gr.update(value="")

    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="teal", neutral_hue="slate"),
        title="Education Sidekick",
        css=".footer { opacity: 0.85; font-size: 0.9rem; }",
    ) as demo:
        gr.Markdown(
            "# Education Sidekick\n"
            "Type your question or goal and **Send**. The coach tailors depth to what you share about your subject and level, "
            "and it’s for **practice and explanations**—not for having graded work done for you."
        )
        if banner:
            gr.Markdown(banner)

        thread = gr.State(make_thread_id())

        with gr.Row():
            chatbot = gr.Chatbot(label="Conversation", height=400, type="messages")
        message = gr.Textbox(
            label="Your message",
            placeholder="Ask for an explanation, study plan, or practice outline…",
            lines=3,
        )
        with gr.Row():
            reset_button = gr.Button("New session", variant="secondary")
            go_button = gr.Button("Send", variant="primary")

        with gr.Column(visible=False) as email_followup:
            gr.Markdown("**Email a copy?** Would you like this conversation sent to your email?")
            with gr.Row() as email_step1:
                email_offer_yes = gr.Button("Yes", variant="primary")
                email_offer_no = gr.Button("No thanks", variant="secondary")
            with gr.Column(visible=False) as email_step2:
                email_capture = gr.Textbox(
                    label="Your email address",
                    placeholder="you@example.com",
                    lines=1,
                )
                email_send_btn = gr.Button("Send copy", variant="secondary")

        email_status = gr.Textbox(label="Email status", interactive=False, lines=2)

        chat_inputs = [
            message,
            chatbot,
            thread,
        ]
        chat_outputs = [chatbot, thread, email_status, email_followup, email_step1, email_step2]

        message.submit(process_message, chat_inputs, chat_outputs)
        go_button.click(process_message, chat_inputs, chat_outputs)

        email_offer_no.click(
            on_email_no,
            [],
            [email_followup, email_step1, email_step2],
        )
        email_offer_yes.click(
            on_email_yes,
            [],
            [email_step1, email_step2],
        )
        email_send_btn.click(
            on_email_send,
            [chatbot, email_capture],
            [email_status, email_followup, email_step1, email_step2, email_capture],
        )

        reset_button.click(
            reset,
            [],
            [
                message,
                chatbot,
                thread,
                email_status,
                email_followup,
                email_step1,
                email_step2,
                email_capture,
            ],
        )

    return demo


def _port_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _resolve_server_port() -> int:
    explicit = os.environ.get("GRADIO_SERVER_PORT") or os.environ.get("PORT")
    if explicit is not None and str(explicit).strip() != "":
        return int(explicit)
    for candidate in range(7860, 7920):
        if _port_available(candidate):
            if candidate != 7860:
                logger.info(
                    "Port 7860 in use; starting Gradio on %s (set GRADIO_SERVER_PORT to choose a port)",
                    candidate,
                )
            return candidate
    raise RuntimeError(
        "No free TCP port in range 7860–7919. Set GRADIO_SERVER_PORT or PORT in your environment."
    )


def launch_local() -> None:
    demo = create_demo()
    port = _resolve_server_port()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
    )


def launch() -> None:
    launch_local()
