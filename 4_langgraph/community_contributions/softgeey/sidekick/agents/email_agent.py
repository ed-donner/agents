"""Email agent node: fetch recent emails and draft replies via LLM."""

from langchain_core.messages import HumanMessage, AIMessage
from llm_client import get_llm
from agents.state import AgentState

EMAIL_SYSTEM = """You are SideKick, a professional AI assistant for a Senior Project Manager at a software development company.

Your email tasks:
- Summarize recent emails clearly and concisely
- Draft professional, context-aware email replies or new emails
- Flag urgent or high-priority messages
- Keep tone: clear, professional, direct

When drafting emails, use this format:
TO: [recipient]
SUBJECT: [subject]
---
[email body]
---
"""


def email_node(state: AgentState) -> dict:
    """
    Handles email intent.
    If Gmail data is available in tool_data, includes it as context.
    """
    llm = get_llm(temperature=0.4)
    last_human = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None
    )

    # Build context from fetched emails if available
    email_context = ""
    emails = state.tool_data.get("emails", [])
    if emails:
        lines = ["Recent emails:\n"]
        for i, e in enumerate(emails[:5], 1):
            lines.append(
                f"{i}. From: {e['from']}\n"
                f"   Subject: {e['subject']}\n"
                f"   Date: {e['date']}\n"
                f"   Preview: {e['snippet']}\n"
            )
        email_context = "\n".join(lines)

    user_message = last_human.content if last_human else ""
    full_prompt = f"{EMAIL_SYSTEM}\n\n{email_context}\n\nUser request: {user_message}"

    response = llm.invoke(full_prompt)
    return {
        "response": response.content,
        "messages": [AIMessage(content=response.content)],
    }
