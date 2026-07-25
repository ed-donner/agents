"""Extract text deltas from LangChain LLM stream chunks."""

from __future__ import annotations

from typing import Any


def chunk_text(chunk: Any) -> str:
    """Return incremental text from an AIMessageChunk (provider-agnostic)."""
    c = getattr(chunk, "content", None)
    if c is None:
        return ""
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(getattr(block, "text", str(block)))
        return "".join(parts)
    return str(c)
