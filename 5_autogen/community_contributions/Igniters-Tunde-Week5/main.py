"""
Customer support simulator — two AutoGen AgentChat agents:
Customer_Sam (role-play) and Support_Riley (empathetic support + fake lookup tools).
Stops when the customer says RESOLVED or ESCALATE, or after a message cap.
"""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.models import ModelFamily, ModelInfo
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

_here = Path(__file__).resolve().parent
load_dotenv(_here / ".env", override=False)
load_dotenv(_here.parent.parent.parent / ".env", override=False)


def _gemini_api_key() -> str | None:
    raw = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    key = raw.strip().strip('"').strip("'")
    return key or None


def _gemini_model() -> str:
    # Must start with "gemini-" so OpenAIChatCompletionClient sets Google's OpenAI-compatible base URL.
    return (os.getenv("GEMINI_MODEL") or "gemini-2.0-flash").strip()


def _fallback_gemini_model_info(model_name: str) -> ModelInfo:
    """autogen-ext only whitelists some Gemini ids; Google adds new names (e.g. gemini-2.5-flash) before the library."""
    family = ModelFamily.GEMINI_2_0_FLASH
    if "2.5" in model_name:
        family = ModelFamily.GEMINI_2_5_FLASH
    elif "1.5" in model_name:
        family = ModelFamily.GEMINI_1_5_FLASH
    return {
        "vision": True,
        "function_calling": True,
        "json_output": True,
        "family": family,
        "structured_output": True,
        "multiple_system_messages": False,
    }


def _make_gemini_client(model_name: str, api_key: str) -> OpenAIChatCompletionClient:
    kwargs: dict = {"model": model_name, "api_key": api_key, "temperature": 0}
    try:
        return OpenAIChatCompletionClient(**kwargs)
    except ValueError as e:
        if "model_info is required" not in str(e):
            raise
        kwargs["model_info"] = _fallback_gemini_model_info(model_name)
        return OpenAIChatCompletionClient(**kwargs)


# Tiny in-memory "backend" — no network, runs locally
_ORDERS = {
    "ORD-1001": "Status: Shipped — tracking TRK9281, ETA in 3 days.",
    "ORD-1002": "Status: Payment failed — card declined. Ask customer to update payment in account settings.",
    "ORD-1003": "Status: Processing — warehouse delay; expected to ship within 2 business days.",
}
_ACCOUNTS = {
    "alex@example.com": "Account active; last login 2 days ago. Password reset allowed.",
    "jamie@example.com": "Account locked after failed logins. Unlock requires email verification.",
}


async def lookup_order(order_id: str) -> str:
    """Look up fake order status. Valid examples: ORD-1001, ORD-1002, ORD-1003."""
    key = (order_id or "").strip().upper()
    return _ORDERS.get(key, "No order on file for that ID. Ask the customer to copy it from their confirmation email.")


async def check_account(email: str) -> str:
    """Look up fake account/login notes. Pass the customer's email address."""
    key = (email or "").strip().lower()
    return _ACCOUNTS.get(key, "No special notes on file; account appears in good standing. Suggest password reset flow.")


def _termination():
    return (
        TextMentionTermination("RESOLVED")
        | TextMentionTermination("ESCALATE")
        | MaxMessageTermination(max_messages=16)
    )


def _build_team(model_client: OpenAIChatCompletionClient) -> SelectorGroupChat:
    customer = AssistantAgent(
        name="Customer_Sam",
        model_client=model_client,
        system_message=(
            "You are a customer chatting with support. You are mildly frustrated but not abusive. "
            "You do NOT know internal systems; you may invent plausible details (order IDs, email) only if natural—"
            "you can reveal ORD-1001 or alex@example.com if the scenario fits. "
            "Keep each reply to one short paragraph unless asked a direct question. "
            "IMPORTANT: You must speak FIRST in this thread—react to the opening complaint in the task. "
            "If support fixes your issue, end a later message with the exact word RESOLVED (all caps) somewhere. "
            "If support is useless after several tries, end with the exact word ESCALATE (all caps)."
        ),
    )
    support = AssistantAgent(
        name="Support_Riley",
        model_client=model_client,
        tools=[lookup_order, check_account],
        system_message=(
            "You are a tier-1 support specialist for an online shop. Be concise, empathetic, and professional. "
            "Ask one clarifying question when needed. Use lookup_order when the customer gives an order ID. "
            "Use check_account when they give an email for login or account issues. "
            "Do NOT speak first—wait until Customer_Sam has messaged. "
            "Never invent tool results; rely on tools. Do not say RESOLVED or ESCALATE—that is only for the customer."
        ),
    )
    return SelectorGroupChat(
        [customer, support],
        model_client=model_client,
        termination_condition=_termination(),
    )


def _task_prompt(user_line: str) -> str:
    return (
        "[Support simulation — Customer_Sam must send the first message]\n\n"
        f"The customer initially says:\n\"{user_line.strip()}\"\n\n"
        "Customer_Sam: respond first in character (paraphrase their complaint, add a tiny detail). "
        "Then Support_Riley may reply. Continue the thread naturally."
    )


def _append_pair(messages: list, user_text: str, assistant_text: str) -> list:
    """Gradio 5+ Chatbot expects list of {role, content} dicts."""
    out = list(messages or [])
    out.append({"role": "user", "content": user_text})
    out.append({"role": "assistant", "content": assistant_text})
    return out


async def run_simulation(user_input: str, history: list):
    key = _gemini_api_key()
    if not key:
        msg = (
            "Set GEMINI_API_KEY or GOOGLE_API_KEY in `.env` (this folder or repo root `agents/.env`) "
            "and restart. Optional: GEMINI_MODEL (default gemini-2.0-flash)."
        )
        yield _append_pair(history, user_input, msg), ""
        return

    if not (user_input or "").strip():
        yield _append_pair(
            history,
            "",
            "Type the customer’s opening line (e.g. “My order never arrived”).",
        ), ""
        return

    messages = list(history or [])
    transcript = ""
    messages = _append_pair(messages, user_input, transcript)

    model_name = _gemini_model()
    if not model_name.startswith("gemini-"):
        model_name = f"gemini-{model_name.lstrip('-')}"
    model_client = _make_gemini_client(model_name, key)
    team = _build_team(model_client)

    try:
        async for event in team.run_stream(task=_task_prompt(user_input)):
            if isinstance(event, TextMessage):
                transcript += f"\n\n**{event.source}**: {event.content}"
                messages[-1] = {"role": "assistant", "content": transcript.strip()}
                yield messages, ""
    except Exception as e:
        err = f"Run failed: {e}"
        messages[-1] = {
            "role": "assistant",
            "content": transcript.strip() + f"\n\n_{err}_",
        }
        yield messages, ""


def main():
    if not _gemini_api_key():
        print("Warning: GEMINI_API_KEY / GOOGLE_API_KEY not set. Add it to .env and restart.")

    with gr.Blocks(title="Customer support simulator") as demo:
        gr.Markdown(
            "## Customer support simulator (AutoGen + Gemini)\n"
            "Uses **Google Gemini** (`GEMINI_API_KEY`). Type the **customer’s opening message**. "
            "**Customer_Sam** and **Support_Riley** role-play; "
            "Riley can call fake tools `lookup_order` / `check_account`. "
            "Try order **ORD-1001** or email **alex@example.com**. "
            "The run ends when the customer says **RESOLVED** or **ESCALATE**, or after 16 messages."
        )
        # Message dicts {role, content} work across Gradio versions; `type=` is only on newer Chatbot APIs.
        chatbot = gr.Chatbot(label="Transcript", height=420)
        msg = gr.Textbox(
            label="Customer opening line",
            placeholder='e.g. "Where is my package? I ordered last week."',
        )
        msg.submit(run_simulation, [msg, chatbot], [chatbot, msg])

    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
