"""RAG-lite tutor: retrieve corpus snippets, then ask OpenAI with grounding."""

from __future__ import annotations

import logging
from pathlib import Path

from kirundi_brain import brain_fs, config

logger = logging.getLogger(__name__)

_SYSTEM = """You are a careful Kirundi (Rundi) language tutor for Burundi.
Use ONLY the provided corpus context for vocabulary and phrasing.
If the context is insufficient, say what is missing and suggest which Brain lesson to open.
Keep answers short: phrase, meaning, one example sentence, pronunciation tip when useful.
Prefer Kirundi orthography used in the corpus."""


def ask_kirundi(root: Path, question: str, learner_level: str = "A1") -> str:
    """Answer a Kirundi question grounded in Brain Markdown + optional OpenAI."""
    q = (question or "").strip()
    if not q:
        return "Error: question is empty."

    context = brain_fs.collect_context(root, q)
    key = config.openai_api_key()
    if not key:
        return (
            "OPENAI_API_KEY is not set. Retrieved corpus context only:\n\n"
            f"{context}"
        )

    try:
        from openai import OpenAI
    except ImportError:
        return "openai package is not installed. Retrieved context only:\n\n" + context

    client = OpenAI(api_key=key)
    user_prompt = (
        f"Learner level: {learner_level}\n\n"
        f"Corpus context:\n{context}\n\n"
        f"Question: {q}"
    )
    try:
        completion = client.chat.completions.create(
            model=config.openai_model(),
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception as exc:
        logger.exception("ask_kirundi OpenAI call failed")
        return f"OpenAI error: {exc}\n\nCorpus context:\n{context}"

    answer = (completion.choices[0].message.content or "").strip()
    return answer or "Model returned an empty answer."


def grade_answer(
    root: Path,
    prompt_en: str,
    learner_reply: str,
    expected_hint: str = "",
) -> str:
    """Grade a short Kirundi reply against corpus-backed expectations."""
    key = config.openai_api_key()
    context = brain_fs.collect_context(root, prompt_en or expected_hint or learner_reply)
    if not key:
        return (
            "OPENAI_API_KEY missing — cannot grade automatically.\n"
            f"Context:\n{context}\n"
            f"Learner said: {learner_reply}"
        )

    try:
        from openai import OpenAI
    except ImportError:
        return "openai package missing."

    client = OpenAI(api_key=key)
    system = (
        "You grade Kirundi learner answers. Reply with:\n"
        "Score: N/10\nCorrected: ...\nFeedback: ...\n"
        "Use corpus context; be encouraging and precise."
    )
    user = (
        f"Prompt (EN): {prompt_en}\n"
        f"Expected hint: {expected_hint or '(none)'}\n"
        f"Learner reply: {learner_reply}\n\n"
        f"Corpus:\n{context}"
    )
    try:
        completion = client.chat.completions.create(
            model=config.openai_model(),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
    except Exception as exc:
        logger.exception("grade_answer OpenAI call failed")
        return f"OpenAI error: {exc}"

    return (completion.choices[0].message.content or "").strip()
