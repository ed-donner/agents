"""
agent.py — LangGraph research pipeline.

Builds two graphs:
  clarifier_graph  — runs the clarifier node once to generate scoping questions
  research_graph   — full pipeline: planner → searcher → sufficiency →
                     writer → evaluator → emailer

Uses SQLite checkpointing so sessions persist across restarts.
Each user's thread_id is the isolation key — different users never share state.
"""
from __future__ import annotations

import asyncio
import os
import sqlite3

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from models import (
    ClarifyingQuestions, ReportEvaluation, ResearchState,
    ResearchSufficiency, SafetyCheck, WebSearchPlan,
)
from tools import send_report_email, web_search

load_dotenv(override=True)


# ── Provider configuration ─────────────────────────────────────────────────────

PROVIDER = os.environ.get("RESEARCH_PROVIDER", "groq")

_PROVIDERS: dict[str, dict] = {
    "groq":       {"model": "llama-3.3-70b-versatile",           "base_url": "https://api.groq.com/openai/v1",    "api_key_env": "GROQ_API_KEY"},
    "cerebras":   {"model": "qwen-3-235b-a22b-instruct-2507",    "base_url": "https://api.cerebras.ai/v1",       "api_key_env": "CEREBRAS_API_KEY"},
    "openrouter": {"model": "meta-llama/llama-3.3-70b-instruct", "base_url": "https://openrouter.ai/api/v1",    "api_key_env": "OPENROUTER_API_KEY"},
    "openai":     {"model": "gpt-4o-mini",                       "base_url": "https://api.openai.com/v1",        "api_key_env": "OPENAI_API_KEY"},
}

_cfg = _PROVIDERS.get(PROVIDER, _PROVIDERS["groq"])

# PR checklist: explicit model parameters per agent role
# temperature controls creativity; max_tokens caps output; top_p controls diversity
_MODEL_PARAMS: dict[str, dict] = {
    "safety":    {"temperature": 0.0, "max_tokens": 256,  "top_p": 1.00},
    "structured":{"temperature": 0.1, "max_tokens": 2048, "top_p": 0.90},
    "default":   {"temperature": 0.3, "max_tokens": 4096, "top_p": 0.95},
    "creative":  {"temperature": 0.6, "max_tokens": 4096, "top_p": 0.95},
}


def _build_llm(role: str = "default") -> ChatOpenAI:
    """Return a ChatOpenAI-compatible LLM for the configured provider and role."""
    p = _MODEL_PARAMS[role]
    return ChatOpenAI(
        model=_cfg["model"],
        base_url=_cfg["base_url"],
        api_key=os.environ.get(_cfg["api_key_env"], ""),
        temperature=p["temperature"],
        max_tokens=p["max_tokens"],
        streaming=True,  # required for on_chat_model_stream events in astream_events
    )


# LangSmith tracing — uses LANGCHAIN_API_KEY, consumes no inference tokens
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"]    = "deep-research-langgraph"
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"


# ── LLM instances — one per role ───────────────────────────────────────────────
default_llm    = _build_llm("default")     # clarifier, planner, sufficiency
creative_llm   = _build_llm("creative")    # writer — higher temperature for prose
structured_llm = _build_llm("structured")  # evaluator — low temperature for consistent scoring
safety_llm_raw = _build_llm("safety")      # safety classifier — deterministic (temp=0)

# with_structured_output uses tool-calling (not json_schema) — compatible with Groq and Cerebras
clarifier_llm   = default_llm.with_structured_output(ClarifyingQuestions)
planner_llm     = default_llm.with_structured_output(WebSearchPlan)
sufficiency_llm = default_llm.with_structured_output(ResearchSufficiency)
evaluator_llm   = structured_llm.with_structured_output(ReportEvaluation)
safety_llm      = safety_llm_raw.with_structured_output(SafetyCheck)


# ── Guardrails ─────────────────────────────────────────────────────────────────

def check_query_safety(query: str) -> SafetyCheck:
    """
    Input guardrail: LLM-based safety classifier.
    Runs before the clarifier. Blocks queries requesting harmful, illegal,
    or harassing content. Fails open (allows request) if the classifier errors.
    """
    try:
        return safety_llm.invoke([
            SystemMessage(
                "Classify whether this research query is safe. "
                "Flag UNSAFE for: instructions to cause harm, illegal activity, "
                "synthesis of dangerous substances, or harassment of private individuals. "
                "Legitimate research on sensitive topics (history, medicine, security) is SAFE."
            ),
            HumanMessage(query),
        ])
    except Exception:
        return SafetyCheck(is_safe=True, reason="classifier unavailable — fail open")


def check_report_quality(report: str) -> tuple[bool, str]:
    """
    Output guardrail: heuristic quality check on the generated report.
    Checks minimum word count and absence of unfilled placeholder text.
    Returns (passed: bool, message: str).
    """
    if not report.strip():
        return False, "Report is empty"
    wc = len(report.split())
    if wc < 200:
        return False, f"Report too short ({wc} words, minimum 200)"
    for placeholder in ["[PLACEHOLDER]", "[TODO]", "TODO:", "FIXME", "[INSERT"]:
        if placeholder in report:
            return False, f"Report contains placeholder text: '{placeholder}'"
    return True, f"Quality check passed ({wc} words)"


# ── Pipeline constants ─────────────────────────────────────────────────────────
MAX_SEARCH_RETRIES = 2
MAX_REPORT_RETRIES = 1
_PIPELINE_NODES    = {"planner", "searcher", "sufficiency", "writer", "evaluator", "emailer"}


# ── Node functions ─────────────────────────────────────────────────────────────

def clarifier_node(state: ResearchState) -> dict:
    """Generate 3 scoping questions and a context summary for the query."""
    result = clarifier_llm.invoke([
        SystemMessage("Generate exactly 3 clarifying questions to focus a research query, and a one-sentence context summary."),
        HumanMessage(state["query"]),
    ])
    return {"clarifying_questions": result.questions[:3], "context_summary": result.context_summary}


def planner_node(state: ResearchState) -> dict:
    """Turn the query + user clarification into a prioritised list of search terms."""
    extra = ""
    if state.get("search_retries", 0) > 0:
        extra = f"\nPrevious searches were insufficient. Expand coverage of: {state.get('search_plan', [])}"
    result = planner_llm.invoke([
        SystemMessage("You are a research planner. Produce 5-8 prioritised web search terms, most important first."),
        HumanMessage(
            f"Research query: {state['query']}\n"
            f"User clarification: {state.get('user_clarification', '')}\n{extra}"
        ),
    ])
    return {"search_plan": result.queries}


async def searcher_node(state: ResearchState) -> dict:
    """Run all planned searches in parallel using DuckDuckGo."""
    async def _one(q: str) -> str:
        try:
            result = await asyncio.to_thread(web_search.invoke, q)
            return f"### {q}\n{result}\n"
        except Exception as exc:
            return f"### {q}\nFailed: {exc}\n"

    parts       = await asyncio.gather(*[_one(q) for q in state["search_plan"][:8]])
    new_results = "\n---\n".join(parts)
    existing    = state.get("search_results", "")
    return {"search_results": (existing + "\n\n" + new_results).strip()}


def sufficiency_node(state: ResearchState) -> dict:
    """Decide if accumulated search results are enough for a thorough report."""
    result = sufficiency_llm.invoke([
        SystemMessage("Assess whether the research evidence is sufficient for a thorough report."),
        HumanMessage(
            f"Query: {state['query']}\nClarification: {state.get('user_clarification', '')}\n\n"
            f"Search results (truncated):\n{state.get('search_results', '')[:5000]}"
        ),
    ])
    retries = state.get("search_retries", 0)
    return {
        "is_sufficient":  result.is_sufficient,
        "search_retries": retries + (0 if result.is_sufficient else 1),
        "search_plan":    result.additional_queries if not result.is_sufficient else state["search_plan"],
    }


def writer_node(state: ResearchState) -> dict:
    """Write a detailed Markdown research report. Incorporates evaluator feedback on retry."""
    feedback_block = ""
    if state.get("report_feedback"):
        feedback_block = (
            f"\nYour previous draft was rejected. Evaluator feedback:\n{state['report_feedback']}\n"
            "Address every point in this revision."
        )
    response = creative_llm.invoke([
        SystemMessage(
            "You are a senior research writer. Produce a detailed Markdown report "
            "(minimum 1000 words) with: executive summary, background, key findings, "
            "analysis, conclusions, and follow-up questions. Cite sources inline."
        ),
        HumanMessage(
            f"Query: {state['query']}\nClarification: {state.get('user_clarification', '')}\n"
            f"{feedback_block}\n\nResearch evidence:\n{state.get('search_results', '')[:8000]}"
        ),
    ])
    return {"report": response.content}


def evaluator_node(state: ResearchState) -> dict:
    """Score the report 0-10. Approve if score >= 7 and all quality criteria are met."""
    result = evaluator_llm.invoke([
        SystemMessage(
            "Score the research report 0-10. Approve (is_approved=True) only if: "
            "score >= 7, at least 800 words, fully addresses the query, and cites sources."
        ),
        HumanMessage(f"Query: {state['query']}\n\nReport:\n{state.get('report', '')}"),
    ])
    retries = state.get("report_retries", 0)
    return {
        "report_score":    result.score,
        "report_feedback": result.feedback,
        "report_approved": result.is_approved,
        "report_retries":  retries + (0 if result.is_approved else 1),
    }


def emailer_node(state: ResearchState) -> dict:
    """Send the approved report via SendGrid."""
    status = send_report_email(
        subject=f"Research Report: {state['query'][:60]}",
        body=state.get("report", ""),
    )
    return {"email_status": status}


# ── Routing functions ──────────────────────────────────────────────────────────

def route_sufficiency(state: ResearchState) -> str:
    """Route to writer if sufficient or retries exhausted; otherwise re-plan."""
    if state.get("is_sufficient") or state.get("search_retries", 0) >= MAX_SEARCH_RETRIES:
        return "writer"
    return "planner"


def route_evaluation(state: ResearchState) -> str:
    """Route to emailer if approved or retries exhausted; otherwise revise."""
    if state.get("report_approved") or state.get("report_retries", 0) >= MAX_REPORT_RETRIES:
        return "emailer"
    return "writer"


# ── Graph construction ─────────────────────────────────────────────────────────

# Graph 1: Clarifier only — runs once to generate scoping questions, no memory needed
_clarifier_builder = StateGraph(ResearchState)
_clarifier_builder.add_node("clarifier", clarifier_node)
_clarifier_builder.add_edge(START, "clarifier")
_clarifier_builder.add_edge("clarifier", END)
clarifier_graph = _clarifier_builder.compile()

# SQLite persistent memory — sessions survive kernel restarts
# Each user's thread_id is the isolation key; different users never share state
_conn      = sqlite3.connect("research_memory.db", check_same_thread=False)
sql_memory = SqliteSaver(_conn)

# Graph 2: Full research pipeline
_research_builder = StateGraph(ResearchState)
_research_builder.add_node("planner",     planner_node)
_research_builder.add_node("searcher",    searcher_node)
_research_builder.add_node("sufficiency", sufficiency_node)
_research_builder.add_node("writer",      writer_node)
_research_builder.add_node("evaluator",   evaluator_node)
_research_builder.add_node("emailer",     emailer_node)

_research_builder.add_edge(START,         "planner")
_research_builder.add_edge("planner",     "searcher")
_research_builder.add_edge("searcher",    "sufficiency")
_research_builder.add_conditional_edges("sufficiency", route_sufficiency, {"writer": "writer", "planner": "planner"})
_research_builder.add_edge("writer",      "evaluator")
_research_builder.add_conditional_edges("evaluator",   route_evaluation,  {"emailer": "emailer", "writer": "writer"})
_research_builder.add_edge("emailer",     END)

research_graph = _research_builder.compile(checkpointer=sql_memory)


# ── Helper coroutines (called by app.py) ───────────────────────────────────────

def _initial_state(query: str, user_clarification: str = "") -> ResearchState:
    """Return a fully initialised ResearchState dict."""
    return ResearchState(
        query=query, clarifying_questions=[], context_summary="",
        user_clarification=user_clarification, search_plan=[], search_results="",
        search_retries=0, is_sufficient=False, report="", report_score=0.0,
        report_feedback="", report_retries=0, report_approved=False, email_status="",
    )


async def run_clarifier(query: str) -> tuple[list[str], str]:
    """Phase 1: generate scoping questions. Returns (questions, context_summary)."""
    result = await clarifier_graph.ainvoke(_initial_state(query))
    return result["clarifying_questions"], result["context_summary"]


async def stream_research(query: str, user_clarification: str, thread_id: str):
    """
    Phase 2: stream node transitions and writer output via astream_events.
    Yields (status, report, score_str, email_str) tuples for Gradio.
    SQLite checkpointer persists every checkpoint under thread_id.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state  = _initial_state(query, user_clarification)
    status = "Safety check passed. Starting pipeline...\n"
    report = ""

    try:
        async for event in research_graph.astream_events(state, config, version="v2"):
            kind = event["event"]
            node = event.get("metadata", {}).get("langgraph_node", "")

            if kind == "on_chain_start" and node in _PIPELINE_NODES:
                status += f"Running: {node}...\n"
                yield status, report, "", ""

            elif kind == "on_chat_model_stream" and node == "writer":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    report += chunk.content
                    yield status, report, "", ""

        final        = research_graph.get_state(config)
        score        = final.values.get("report_score", 0.0)
        email_status = final.values.get("email_status", "")

        passed, msg = check_report_quality(report)
        if not passed:
            status += f"Output guardrail warning: {msg}\n"

        wc = len(report.split())
        status += f"Done. {wc} words | Score: {score}/10 | Email: {email_status}\n"
        yield status, report, f"{score}/10", email_status

    except Exception as exc:
        yield f"Pipeline error: {exc}\n{status}", report, "", ""


async def load_session(thread_id: str) -> tuple[str, str]:
    """Load a previous session from SQLite by thread_id. Returns (report, score_str)."""
    try:
        config   = {"configurable": {"thread_id": thread_id.strip()}}
        snapshot = research_graph.get_state(config)
        if not snapshot or not snapshot.values:
            return "Session not found — check the ID.", ""
        report = snapshot.values.get("report", "No report in this session.")
        score  = snapshot.values.get("report_score", 0.0)
        return report, f"{score}/10"
    except Exception as exc:
        return f"Error loading session: {exc}", ""
