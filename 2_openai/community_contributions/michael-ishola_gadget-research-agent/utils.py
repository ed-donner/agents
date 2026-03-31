"""Utility functions for BudgetBuy agents."""

from agents import TResponseInputItem

def _extract_text_from_content(content: object) -> str:
    """Normalize SDK message content payloads into plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
                continue
            if isinstance(item, dict):
                text_value = item.get("text")
                if isinstance(text_value, str):
                    chunks.append(text_value)
                    continue
                # Some SDK payloads nest text under input_text.
                input_text = item.get("input_text")
                if isinstance(input_text, str):
                    chunks.append(input_text)
        return "\n".join(c for c in chunks if c).strip()
    return ""


def extract_last_user_text(message: list[TResponseInputItem]) -> str:
    """Pick the latest user message from conversation items."""
    if not message:
        return ""

    for item in reversed(message):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "user":
            continue
        text = _extract_text_from_content(item.get("content", ""))
        if text.strip():
            return text.strip()
    return ""
