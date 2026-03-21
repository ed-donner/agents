"""Deterministic merge of clarification Q/A into canonical question text (plan.md Phase D)."""

from __future__ import annotations

import re
from collections.abc import Sequence


def merge_clarifications(
    original: str,
    questions: list[str],
    answers: str | list[str],
) -> str:
    """Build an expanded question string for re-triage.

    **Pairing ``answers`` with ``questions``:**
    - If ``answers`` is a ``list[str]``, values are paired in order with ``questions`` (missing
      entries treated as empty).
    - If ``answers`` is a single ``str``:
      - One line per non-empty line → paired in order with ``questions``.
      - If there is exactly one line but several questions, split that line on ``.``-bounded
        boundaries (regex ``\\.\\s+``) into segments; if there are enough segments, pair those.
      - Otherwise the full string is attached to the first question only (rest empty).

    **Empty answers:** Whitespace-only segments are stored as *(no answer provided)* in the
    merged text so re-triage still sees which prompts were skipped.

    **Long answers:** No truncation; the full text is included in the merged document.
    """
    original = original.strip()
    if not questions:
        return original

    pairs = _pair_questions_answers(questions, answers)
    parts = [original, "", "### User clarifications", ""]
    for q, a in pairs:
        a_stripped = a.strip()
        display_a = a_stripped if a_stripped else "*(no answer provided)*"
        parts.append(f"- **Q:** {q}")
        parts.append(f"  **A:** {display_a}")
        parts.append("")
    return "\n".join(parts).strip()


def _pair_questions_answers(
    questions: list[str],
    answers: str | list[str],
) -> list[tuple[str, str]]:
    n = len(questions)
    if isinstance(answers, str):
        return _pair_from_string(questions, answers)
    if not isinstance(answers, Sequence):
        raise TypeError("answers must be str or list[str]")
    alist = [str(x) for x in answers]
    alist.extend([""] * (n - len(alist)))
    return list(zip(questions, alist[:n], strict=False))


def _pair_from_string(questions: list[str], answers: str) -> list[tuple[str, str]]:
    n = len(questions)
    s = answers.strip()
    if not s:
        return [(q, "") for q in questions]

    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    if len(lines) >= n:
        return [(questions[i], lines[i]) for i in range(n)]

    if n == 1:
        return [(questions[0], s)]

    if len(lines) == 1:
        parts = [p.strip() for p in re.split(r"\.\s+", lines[0]) if p.strip()]
        if len(parts) >= n:
            return [(questions[i], parts[i]) for i in range(n)]

    out: list[tuple[str, str]] = [(questions[0], s)]
    out.extend((q, "") for q in questions[1:])
    return out
