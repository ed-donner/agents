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
import pathlib

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
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
    # safety: deterministic single-label output — 256 is more than enough
    "safety":    {"temperature": 0.0, "max_tokens": 256,  "top_p": 1.00},
    # structured: evaluator returns a score + short feedback — 1024 is sufficient
    "structured":{"temperature": 0.1, "max_tokens": 1024, "top_p": 0.90},
    # default: clarifier (3 questions), planner (8 terms), sufficiency (verdict + gaps)
    # none of these need more than ~512 tokens of output
    "default":   {"temperature": 0.3, "max_tokens": 1024, "top_p": 0.95},
    # creative: writer produces a 1000+ word report — needs the most headroom
    "creative":  {"temperature": 0.6, "max_tokens": 2500, "top_p": 0.95},
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


# LangSmith tracing — reads LANGSMITH_API_KEY (current name) or LANGCHAIN_API_KEY (legacy).
# Consumes no inference tokens; traces are visible at smith.langchain.com.
_ls_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
if _ls_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"]     = _ls_key   # SDK reads this name internally
    # Respect endpoint from .env (eu.api.smith.langchain.com) or fall back to default
    if not os.environ.get("LANGCHAIN_ENDPOINT"):
        _ep = os.environ.get("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        os.environ["LANGCHAIN_ENDPOINT"] = _ep
    # Use project name from .env if set, otherwise use a sensible default
    if not os.environ.get("LANGCHAIN_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGSMITH_PROJECT", "deep-research-langgraph")
    print(f"LangSmith tracing enabled → project: {os.environ['LANGCHAIN_PROJECT']}")
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    print("LangSmith tracing disabled (no LANGSMITH_API_KEY found)")


# ── LLM instances — one per role ───────────────────────────────────────────────
default_llm    = _build_llm("default")     # clarifier, planner, sufficiency
creative_llm   = _build_llm("creative")    # writer — higher temperature for prose
structured_llm = _build_llm("structured")  # evaluator — low temperature for consistent scoring
safety_llm_raw = _build_llm("safety")      # safety classifier — deterministic (temp=0)

# method="function_calling" forces tool-calling mode (not json_schema).
# This is the only structured-output method supported by Groq and Cerebras.
# OpenAI also supports it, so this setting works across all providers.
_SO = {"method": "function_calling"}
clarifier_llm   = default_llm.with_structured_output(ClarifyingQuestions, **_SO)
planner_llm     = default_llm.with_structured_output(WebSearchPlan,        **_SO)
sufficiency_llm = default_llm.with_structured_output(ResearchSufficiency,  **_SO)
evaluator_llm   = structured_llm.with_structured_output(ReportEvaluation,  **_SO)
safety_llm      = safety_llm_raw.with_structured_output(SafetyCheck,       **_SO)


# ── Input length limits ────────────────────────────────────────────────────────
# Keep inputs well within free-tier model context windows (typically 4K–8K tokens).
# These character limits are conservative: 1 token ≈ 4 characters.

_LIMITS = {
    "query":         (10,  600),   # min / max characters
    "clarification": (0,   800),
    "extra_context": (0,   600),
}
_COMBINED_MAX = 1800  # sum of all three fields; leaves headroom for system prompts


def validate_inputs(
    query: str,
    clarification: str = "",
    extra_context: str = "",
) -> tuple[bool, str]:
    """
    Input length guardrail — called before the safety check and before the pipeline.
    Returns (is_valid: bool, error_message: str).
    Prevents context-window overflows and prompt-injection via extremely long inputs.
    """
    q  = query.strip()
    cl = clarification.strip()
    ec = extra_context.strip()

    min_q, max_q = _LIMITS["query"]
    if len(q) < min_q:
        return False, f"Query is too short (minimum {min_q} characters)."
    if len(q) > max_q:
        return False, (
            f"Query is too long ({len(q)} characters). "
            f"Please keep it under {max_q} characters — be concise about the topic."
        )

    _, max_cl = _LIMITS["clarification"]
    if len(cl) > max_cl:
        return False, (
            f"Clarification is too long ({len(cl)} characters). "
            f"Please keep it under {max_cl} characters."
        )

    _, max_ec = _LIMITS["extra_context"]
    if len(ec) > max_ec:
        return False, (
            f"Additional context is too long ({len(ec)} characters). "
            f"Please keep it under {max_ec} characters."
        )

    combined = len(q) + len(cl) + len(ec)
    if combined > _COMBINED_MAX:
        return False, (
            f"Total input is too long ({combined} characters across all fields). "
            f"Please reduce to under {_COMBINED_MAX} characters combined."
        )

    return True, ""


# ── Guardrails ─────────────────────────────────────────────────────────────────

def _prompt_guard_check(query: str) -> SafetyCheck | None:
    """
    Layer 1: Llama Prompt Guard 2 86M via Groq.

    Prompt Guard 2 is a 86M-parameter BERT-style classifier trained specifically
    to detect two threat types:
      - INJECTION  : prompt injection — malicious instructions hidden in the text
                     (e.g. "ignore previous instructions and do X instead")
      - JAILBREAK  : jailbreak attempts — requests designed to bypass safety guidelines
                     (e.g. "pretend you have no restrictions")

    It is NOT a general content-safety model, so it is paired with an LLM fallback
    (layer 2) that catches harmful research requests that are phrased normally.

    Returns a SafetyCheck if the call succeeds, or None if Groq is unavailable
    so the caller can fall through to the LLM-based check.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return None
    try:
        from groq import Groq
        client   = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="meta-llama/llama-prompt-guard-2-86m",
            messages=[{"role": "user", "content": query}],
        )
        # The model returns a float probability (0–1) of the input being a jailbreak/injection.
        # Threshold 0.5: above = unsafe, below = safe.
        raw     = response.choices[0].message.content.strip()
        score   = float(raw)
        is_safe = score < 0.5
        pct     = f"{score * 100:.1f}%"
        reason  = f"Prompt Guard 2 jailbreak probability: {pct}"
        return SafetyCheck(is_safe=is_safe, reason=reason)
    except Exception as exc:
        # Groq unavailable or model not found — caller will use LLM fallback
        return None


def _llm_safety_check(query: str) -> SafetyCheck:
    """
    Layer 2: general LLM-based content safety check.

    Catches harmful research requests that are phrased as normal questions
    (e.g. "how do I synthesize sarin") which Prompt Guard 2 would miss
    because they contain no injection or jailbreak language.
    Fails open if the LLM itself errors — so the user is never silently blocked.
    """
    try:
        return safety_llm.invoke([
            SystemMessage(
                "Classify whether this research query is safe to research. "
                "Flag UNSAFE only for: explicit instructions to cause physical harm, "
                "synthesis of chemical/biological weapons, or targeted harassment of "
                "private individuals. Sensitive but legitimate topics such as history, "
                "medicine, cybersecurity, and policy are always SAFE."
            ),
            HumanMessage(query),
        ])
    except Exception:
        return SafetyCheck(is_safe=True, reason="LLM classifier unavailable — fail open")


def check_query_safety(query: str) -> SafetyCheck:
    """
    Two-layer input guardrail:
      1. Llama Prompt Guard 2 86M (Groq) — catches injection and jailbreak phrasing
      2. LLM-based classifier          — catches harmful content requests
    Both layers must pass. Falls open if both are unavailable.
    """
    # Layer 1 — injection / jailbreak detection
    pg_result = _prompt_guard_check(query)
    if pg_result is not None and not pg_result.is_safe:
        return pg_result  # blocked by Prompt Guard 2

    # Layer 2 — harmful content detection (runs even if layer 1 passed / was skipped)
    return _llm_safety_check(query)


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

# DB path for async SQLite persistence
# Absolute path — always points to the same file regardless of launch directory
_DB_PATH = str(pathlib.Path(__file__).parent / "research_memory.db")

# Graph 1: Clarifier only — stateless, no checkpointer needed
_clarifier_builder = StateGraph(ResearchState)
_clarifier_builder.add_node("clarifier", clarifier_node)
_clarifier_builder.add_edge(START, "clarifier")
_clarifier_builder.add_edge("clarifier", END)
clarifier_graph = _clarifier_builder.compile()

# Graph 2: Full research pipeline builder — compiled on demand inside async context managers
# so AsyncSqliteSaver (which must be used via `async with`) can be the checkpointer.
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

# Module-level graph compiled with MemorySaver — used only for graph visualisation
# in the notebook. Actual runs use AsyncSqliteSaver compiled inside each async helper.
research_graph = _research_builder.compile(checkpointer=MemorySaver())


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

    AsyncSqliteSaver must be used via `async with` — we open it here and compile
    a fresh graph for each run so the checkpointer is properly initialised.
    Sessions are persisted to SQLite under thread_id and survive app restarts.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state  = _initial_state(query, user_clarification)
    status = "Safety check passed. Starting pipeline...\n"
    report = ""

    try:
        async with AsyncSqliteSaver.from_conn_string(_DB_PATH) as saver:
            graph = _research_builder.compile(checkpointer=saver)

            async for event in graph.astream_events(state, config, version="v2"):
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

            final        = await graph.aget_state(config)
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
    tid = thread_id.strip()
    if not tid:
        return "Please paste a session ID first.", ""
    try:
        config = {"configurable": {"thread_id": tid}}
        async with AsyncSqliteSaver.from_conn_string(_DB_PATH) as saver:
            graph    = _research_builder.compile(checkpointer=saver)
            snapshot = await graph.aget_state(config)

        if not snapshot or not snapshot.values:
            return (
                f"No session found for ID: {tid}\n\n"
                "This happens if:\n"
                "- The ID was copied incorrectly\n"
                "- The session was run before the current app started (old lambda IDs)\n"
                "- The research failed before any checkpoint was saved\n\n"
                "Copy your session ID from the top of the page during an active run.",
                ""
            )

        report = snapshot.values.get("report", "")
        score  = snapshot.values.get("report_score", 0.0)
        query  = snapshot.values.get("query", "unknown query")

        if not report:
            return (
                f"Session found for: '{query}'\n"
                "The pipeline did not reach the writer stage — no report was saved.\n"
                "Start a new run with the same topic.",
                ""
            )

        return report, f"{score}/10"
    except Exception as exc:
        return f"Error loading session: {exc}", ""
