import re
from exceptions import BadInputError

MAX_LENGTH = 8_000
MIN_LENGTH = 3

BLOCKED_PHRASES = [
    "ignore previous",
    "ignore all previous",
    "disregard previous",
    "system prompt",
    "you are now",
    "new instructions:",
    "developer mode",
    "jailbreak",
]


def check_query(raw: str) -> str:
    """Clean up the query and reject anything obviously bad. Returns the cleaned text."""

    text = (raw or "").strip()

    if not text:
        raise BadInputError("Please enter a research topic.")

    if len(text) < MIN_LENGTH:
        raise BadInputError(f"Too short — need at least {MIN_LENGTH} characters.")

    if len(text) > MAX_LENGTH:
        raise BadInputError(f"Too long — keep it under {MAX_LENGTH:,} characters.")

    lowered = text.lower()
    for phrase in BLOCKED_PHRASES:
        if phrase in lowered:
            raise BadInputError("That looks like a prompt injection — just describe a normal topic.")

    text = re.sub(r"\s+", " ", text)
    return text
