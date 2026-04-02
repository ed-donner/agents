#!/usr/bin/env python3
"""
Week 3 — CrewAI multi-agent assessment.

Three agents (sequential crew):
  1) Research — scan opportunity areas for digital payments + inclusion
  2) Risk & trust — regulatory, fraud, and reliability concerns
  3) Synthesizer — short executive-style brief with recommendations

Loads API keys from the repo-root `agents/.env` (OPENAI_API_KEY).
OpenRouter-style keys (sk-or-*) set OPENAI_API_BASE for LiteLLM/CrewAI compatibility.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv

# Repo root = .../agents
_REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")


def _ensure_llm_env() -> None:
    key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        print(
            "Missing OPENAI_API_KEY (or OPENROUTER_API_KEY). "
            f"Add to {_REPO_ROOT / '.env'}",
            file=sys.stderr,
        )
        sys.exit(1)
    if key.startswith("sk-or-"):
        os.environ.setdefault("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
    elif base := os.getenv("OPENAI_BASE_URL"):
        os.environ.setdefault("OPENAI_API_BASE", base)


DEFAULT_TOPIC = (
    "How digital payments and responsible AI agents could improve financial inclusion "
    "in emerging markets, without increasing fraud or excluding vulnerable users."
)


def run_crew(topic: str | None = None) -> str:
    _ensure_llm_env()
    topic = (topic or os.getenv("CREW_TOPIC") or DEFAULT_TOPIC).strip()

    researcher = Agent(
        role="Payments & Inclusion Research Analyst",
        goal=(
            "Identify concrete opportunity areas where digital payments and automation "
            "can expand access to financial services for underserved populations."
        ),
        backstory=(
            "You follow fintech, mobile money, and policy trends. You cite realistic "
            "mechanisms (wallets, agent networks, KYC, interoperability) not buzzwords."
        ),
        verbose=True,
        allow_delegation=False,
    )

    risk_lead = Agent(
        role="Risk, Fraud & Trust Specialist",
        goal=(
            "Stress-test the research: highlight regulatory, operational, and fraud risks "
            "that could undermine inclusion goals."
        ),
        backstory=(
            "You have worked with regulated payments and incident response. You ask "
            "what breaks first when scale or incentives go wrong."
        ),
        verbose=True,
        allow_delegation=False,
    )

    synthesizer = Agent(
        role="Executive Brief Writer",
        goal=(
            "Deliver a concise, decision-ready summary for a product or strategy lead."
        ),
        backstory=(
            "You write crisp briefs: situation, options, risks, and 3–5 actionable recommendations."
        ),
        verbose=True,
        allow_delegation=False,
    )

    research_task = Task(
        description=(
            f"Research brief request:\n{topic}\n\n"
            "Produce structured notes: (1) key opportunities, (2) example use cases, "
            "(3) stakeholders, (4) metrics that would show progress. "
            "Stay under ~500 words; no need for live web if uncertain—state assumptions."
        ),
        expected_output="Structured research notes with the four sections above.",
        agent=researcher,
    )

    risk_task = Task(
        description=(
            "Using the research notes as input, list the top risks and mitigations: "
            "regulatory, fraud/scams, model/agent errors, data privacy, and user harm. "
            "Be specific. Under ~400 words."
        ),
        expected_output="Risk register style: bullet risks with mitigations.",
        agent=risk_lead,
        context=[research_task],
    )

    synthesis_task = Task(
        description=(
            "Combine the research and risk analysis into one executive brief: "
            "Executive summary (3–4 sentences), Key opportunities, Top risks, "
            "Recommendations (numbered). Tone: professional, suitable for LinkedIn or internal memo. "
            "Max ~600 words."
        ),
        expected_output="Single markdown document with the sections requested.",
        agent=synthesizer,
        context=[research_task, risk_task],
    )

    crew = Crew(
        agents=[researcher, risk_lead, synthesizer],
        tasks=[research_task, risk_task, synthesis_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff(inputs={"topic": topic})
    text = getattr(result, "raw", None) or str(result)

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    report = out_dir / "week3_payment_inclusion_brief.md"
    report.write_text(f"# Week 3 CrewAI output\n\n**Topic:** {topic}\n\n{text}\n", encoding="utf-8")
    print(f"\nWrote {report}\n")
    return text


if __name__ == "__main__":
    arg_topic = " ".join(sys.argv[1:]).strip() or None
    run_crew(arg_topic)
