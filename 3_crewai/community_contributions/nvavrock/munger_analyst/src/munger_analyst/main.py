#!/usr/bin/env python
import sys
import warnings
from datetime import datetime

from pydantic import BaseModel, Field

from crewai import LLM

from munger_analyst.crew import MungerAnalyst
from munger_analyst.memo_naming import (
    build_inputs,
    find_latest_memo,
    list_saved_memos,
    load_memo_text,
)

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DISCLAIMER = (
    "Educational business analysis only — not personalized financial advice."
)


def run():
    """
    Run the crew.
    """
    company = input("Enter the company name for research: ")
    inputs = build_inputs(company)

    try:
        MungerAnalyst().crew().kickoff(inputs=inputs)
        print(f"Memo written to {inputs['memo_path']}")
        print(DISCLAIMER)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = build_inputs("Costco")
    try:
        MungerAnalyst().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        MungerAnalyst().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = build_inputs("Costco")

    try:
        MungerAnalyst().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception(
            "No trigger payload provided. Please provide JSON payload as argument."
        )

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    company = (
        trigger_payload.get("company")
        or trigger_payload.get("topic")
        or ""
    )
    inputs = build_inputs(company)
    inputs["crewai_trigger_payload"] = trigger_payload

    try:
        result = MungerAnalyst().crew().kickoff(inputs=inputs)
        print(f"Memo written to {inputs['memo_path']}")
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")


class RouteDecision(BaseModel):
    intent: str = Field(description="One of: analyze, followup, clarify, end")
    company: str = Field(
        default="",
        description="Company or ticker if the user named one; else empty",
    )
    reply_hint: str = Field(
        default="",
        description="Short clarifying question if intent is clarify",
    )


def _router_llm() -> LLM:
    return LLM(model="openai/gpt-4o-mini")


def _decide_route(
    user_message: str,
    has_memo: bool,
    last_company: str,
    saved_memo_names: str,
) -> RouteDecision:
    llm = _router_llm()
    prompt = f"""You route a munger-analyst chatbot.

User message: {user_message!r}
Has prior memo in session: {has_memo}
Last analyzed company: {last_company!r}
Saved memos on disk (can answer follow-ups without re-running): {saved_memo_names}

Choose intent:
- analyze: user wants a fresh deep analysis of a company/ticker
- followup: user asks about a prior memo / company (session or saved on disk)
- clarify: missing company name or the ask is too vague
- end: user wants to quit

If the user mentions a company/ticker that has a saved memo (e.g. GIS / General Mills),
prefer followup and set company to that name.
Return structured fields only.
"""
    return llm.call(
        messages=[{"role": "user", "content": prompt}],
        response_model=RouteDecision,
    )


def _answer_followup(user_message: str, company: str, memo: str) -> str:
    llm = _router_llm()
    prompt = f"""You are a Munger-style business analyst chatbot.
Company: {company}
Prior memo:
---
{memo}
---
User follow-up: {user_message}

Answer using the memo and mental-model framing. If the memo lacks the answer, say what is missing.
Keep it concise. Remind once that this is educational analysis, not financial advice.
Lead with the bottom line when relevant (BLUF).
"""
    return llm.call(messages=[{"role": "user", "content": prompt}])


def _resolve_memo(company: str, last_company: str, last_memo: str) -> tuple[str, str] | None:
    """Return (company_label, memo_text) from session or disk."""
    if last_memo and (
        not company
        or company.lower() in last_company.lower()
        or last_company.lower() in company.lower()
    ):
        return last_company or company, last_memo

    target = company or last_company
    if not target:
        return None
    path = find_latest_memo(target)
    if path is None:
        return None
    return target, load_memo_text(path)


def chat():
    """Interactive chatbot: route to deep analysis crew or follow-ups on memos."""
    print("Munger Analyst chatbot (Munger mental models)")
    print("Commands: type a company to analyze, ask follow-ups, or 'exit' to quit.")
    print("Memos save as output/YYYYMMDD_<company>_memo.md (BLUF: verdict first).")
    saved = list_saved_memos()
    if saved:
        print("Saved memos available for chat:")
        for path in saved[:12]:
            print(f"  - {path.name}")
    print(DISCLAIMER)
    print()

    last_company = ""
    last_memo = ""

    while True:
        try:
            user_message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break

        saved_names = ", ".join(p.name for p in list_saved_memos()[:20]) or "(none)"
        decision = _decide_route(
            user_message, bool(last_memo), last_company, saved_names
        )
        intent = (decision.intent or "clarify").lower().strip()

        if intent == "end":
            print("Assistant: Goodbye.")
            break

        if intent == "clarify":
            hint = decision.reply_hint or (
                "Which company or ticker should I analyze?"
            )
            print(f"Assistant: {hint}")
            continue

        if intent == "followup":
            resolved = _resolve_memo(decision.company, last_company, last_memo)
            if resolved is None:
                print(
                    "Assistant: No matching memo found. "
                    "Name a company to analyze, or ask about one with a saved memo "
                    f"({saved_names})."
                )
                continue
            company_label, memo_text = resolved
            last_company = company_label
            last_memo = memo_text
            reply = _answer_followup(user_message, company_label, memo_text)
            print(f"Assistant:\n{reply}\n")
            continue

        company = (decision.company or user_message).strip()
        if not company:
            print("Assistant: Which company or ticker should I analyze?")
            continue

        print(f"Assistant: Running deep analysis on {company}…")
        inputs = build_inputs(company)
        try:
            result = MungerAnalyst().crew().kickoff(inputs=inputs)
            last_company = company
            last_memo = result.raw
            print(f"Assistant:\n{last_memo}\n")
            print(f"Memo written to {inputs['memo_path']}")
            print(DISCLAIMER)
        except Exception as e:
            print(f"Assistant: Analysis failed: {e}")
