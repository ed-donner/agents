"""LangGraph deep-research pipeline"""

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any, Literal

import httpx
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field
import requests
from typing_extensions import TypedDict

# Constants
DATA_DIR = Path('./data')
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DB_PATH = (DATA_DIR / "memory.db").resolve()

MAX_RESEARCH_TURNS = 20
DEFAULT_PHRASES_COUNT = 5
MAX_TRIAGE_ROUNDS = 3
MAX_EVALUATOR_RETRIES = 2

PUSHOVER_MESSAGES_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_NOTIFY_MESSAGE = "Research job finished"

llm = init_chat_model("openai:gpt-5-nano")


# Pydantic models
class TriageResults(BaseModel):
    is_ambiguous: bool = Field(description="Whether the query is ambiguous")
    what_is_ambiguous: list[str] = Field(
        description="List of things that are ambiguous in the query",
    )


class ClarificationQuestion(BaseModel):
    question: str = Field(description="One focused follow-up question to resolve ambiguity")


class SearchItem(BaseModel):
    query: str = Field(description="The search term to use")
    reason: str = Field(description="Why this search is important")


class SearchPlan(BaseModel):
    searches: list[SearchItem] = Field(description="List of web searches to perform")


class ResearchItem(BaseModel):
    query: str = Field(description="The search term to use")
    reason: str = Field(description="Why this search is important")
    result: str = Field(description="The result of the search")


class ResearchData(BaseModel):
    results: list[ResearchItem] = Field(description="Results of the web searches")


class Report(BaseModel):
    markdown_report: str = Field(description="Markdown formatted body of the report.")
    summary: str = Field(description="Summary addressing original question.")


class EvaluationResult(BaseModel):
    passes: bool = Field(description="Whether the report is acceptable.")
    gaps: list[str] = Field(
        default_factory=list,
        description="Concrete shortcomings if passes is false.",
    )
    suggested_searches: list[str] = Field(
        default_factory=list,
        description="Web search queries to improve the report if passes is false.",
    )

# State
class GraphState(TypedDict, total=False):
    query: str
    user_clarifications: str
    canonical: str
    triage: TriageResults
    pending_clarification_question: str
    plan: SearchPlan
    research_delta: ResearchData
    research_accum: ResearchData
    report: Report
    last_eval: EvaluationResult
    round_idx: int
    terminal_outcome: str



# Instructions
def _triage_instruction() -> str:
    return """You are query Triager tasked with inspecting the query for ambiguity.

If the query is clear and unambiguous, return TriageResults with is_ambiguous set to False.
If the query is ambiguous, return TriageResults with is_ambiguous set to True and a list of things that are ambiguous in the query.
"""


def _clarifier_instruction() -> str:
    return """You are a Clarification Agent. Given an ambiguous query and a list of ambiguous aspects,
output exactly ONE focused follow-up question the user should answer. Be concise.
"""


def _planner_instruction() -> str:
    return """You are a research planning agent. Your task is to prepare a number of web search phases helpful to best answer the question.
Make sure to cover all the aspects of the question. Provide reason for each search phrase."""


def _research_instruction() -> str:
    return f"""You are a research agent. Your task is to perform a number of web searches from the list of provided search topics.
You are given a curated list of search topics. For each item in the list, perform a web search for the query and produce a concise summary.

Keep summaries to 3-4 paragraphs and under 500 words. Use guidance from the reason clause for the search to produce succinct and to-the-point summary.
Copy the reason verbatim from input to the output.

# Date
{datetime.now().strftime('%Y-%m-%d')}
"""


def _report_instruction() -> str:
    return """You are Senior Researcher writing a comprehensive report. Your task is to generate markdown-formatted report based on the research materials.
You will be given:
 * Original question
 * Research materials containing results of prior searches

Your task is to synthesize the research materials into a comprehensive report that addresses the original question. Aim for 1000+ words long report.
Make sure that the report is:
 * Comprehensive and well-structured
 * Clearly written and easy to follow
 * If it references any measurable values, keep the units the same (convert if needed)
"""


def _evaluator_instruction() -> str:
    return """You are a strict research quality evaluator.

Given the user's original question, the research material gathered, and the draft markdown report:
- Decide whether the report **fully and accurately** answers the question using the evidence available.
- If it passes, set passes=true and use empty lists for gaps and suggested_searches.
- If it fails, set passes=false, list concrete **gaps** (missing coverage, weak sourcing, factual issues), and suggest **short web search queries** (suggested_searches) that would help fix the report.

Be concise: gaps are short bullet-style strings; suggested_searches are query strings only."""


# Runners
async def run_triage(canonical_question: str) -> TriageResults:
    print("[Triage] checking query...")
    structured = llm.with_structured_output(TriageResults)
    out = await structured.ainvoke(
        [
            SystemMessage(content=_triage_instruction()),
            HumanMessage(content=f"# Query\n{canonical_question}"),
        ]
    )
    if out.is_ambiguous:
        print("[Triage] ambiguous - needs clarification")
    else:
        print("[Triage] clear - proceeding")
    return out


async def run_clarifier(canonical_question: str, aspects: list[str]) -> str:
    print("[Clarifier] drafting one follow-up question...")
    structured = llm.with_structured_output(ClarificationQuestion)
    payload = (
        f"# Original Query\n{canonical_question}\n\n"
        f"# Ambiguous Aspects Found\n{aspects}\n\n"
        "Respond with exactly one follow-up question."
    )
    out = await structured.ainvoke(
        [
            SystemMessage(content=_clarifier_instruction()),
            HumanMessage(content=payload),
        ]
    )
    print("[Clarifier] done")
    return out.question.strip()


async def run_planner(canonical_question: str, phrases_count: int) -> SearchPlan:
    print("[Planner] building search plan...")
    structured = llm.with_structured_output(SearchPlan)
    inp = (
        f"# Question\n{canonical_question}\n\n"
        f"Provide {phrases_count} web search phrases to best answer the question."
    )
    plan = await structured.ainvoke(
        [
            SystemMessage(content=_planner_instruction()),
            HumanMessage(content=inp),
        ]
    )
    print(f"[Planner] done ({len(plan.searches)} searches)")
    return plan


async def run_report(canonical_question: str, research: ResearchData) -> Report:
    print("[Report] writing draft...")
    structured = llm.with_structured_output(Report)
    inp = (
        f"# Original Question\n{canonical_question}\n\n"
        f"# Research Materials\n{research.model_dump_json()}"
    )
    out = await structured.ainvoke(
        [
            SystemMessage(content=_report_instruction()),
            HumanMessage(content=inp),
        ]
    )
    print("[Report] done")
    return out


async def run_evaluator(
    canonical_question: str,
    report: Report,
    research: ResearchData,
) -> EvaluationResult:
    print("[Evaluator] reviewing draft...")
    structured = llm.with_structured_output(EvaluationResult)
    inp = (
        f"# Original Question\n{canonical_question}\n\n"
        f"# Research Materials\n{research.model_dump_json()}\n\n"
        f"# Draft Report (markdown)\n{report.markdown_report}\n\n"
        f"# Summary\n{report.summary}\n"
    )
    ev = await structured.ainvoke(
        [
            SystemMessage(content=_evaluator_instruction()),
            HumanMessage(content=inp),
        ]
    )
    if ev.passes:
        print("[Evaluator] pass")
    else:
        print("[Evaluator] fail - draft not acceptable (retry if rounds remain)")
    return ev


# Tools
async def serper_search(query: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://google.serper.dev/search",
            json={"q": query},
            headers={"X-API-KEY": os.environ["SERPER_API_KEY"]},
        )
        r.raise_for_status()
        data = r.json()
    organic = data.get("organic") or []
    parts: list[str] = []
    for i, item in enumerate(organic[:10], 1):
        title = item.get("title") or ""
        snippet = item.get("snippet") or ""
        link = item.get("link") or ""
        parts.append(f"{i}. {title}\n{snippet}\n{link}")
    return "\n\n".join(parts) if parts else str(data)[:8000]

@tool
async def web_search(query: str) -> str:
    """Search the web and return a plain-text block of results."""
    q = query.strip()
    preview = q if len(q) <= 70 else q[:67] + "..."
    print(f"[Serper] {preview}")
    return await serper_search(query)


def _tool_call_arguments(tc: dict[str, Any]) -> dict[str, Any]:
    raw = tc.get("args")
    if isinstance(raw, str):
        return json.loads(raw) if raw.strip() else {}
    return raw or {}


async def _web_search_tool_message(tc: dict[str, Any]) -> ToolMessage:
    if tc["name"] != "web_search":
        raise RuntimeError(f"Unexpected tool: {tc['name']}")
    q = str(_tool_call_arguments(tc).get("query", ""))
    text = await web_search.ainvoke({"query": q})
    return ToolMessage(content=text, tool_call_id=tc["id"])


def merge_research(a: ResearchData, b: ResearchData) -> ResearchData:
    merged = ResearchData(results=list(a.results) + list(b.results))
    print(f"[Merge] {len(a.results)} + {len(b.results)} -> {len(merged.results)} results")
    return merged


async def build_retry_search_plan(
    canonical_question: str,
    ev: EvaluationResult,
) -> SearchPlan:
    print("[Retry plan] building supplemental searches...")
    trimmed = [s.strip() for s in ev.suggested_searches if s.strip()]
    if trimmed:
        items = [
            SearchItem(
                query=q[:500],
                reason="Evaluator-suggested search to address report gaps.",
            )
            for q in trimmed[:DEFAULT_PHRASES_COUNT]
        ]
        print(f"[Retry plan] using {len(items)} evaluator-suggested queries")
        return SearchPlan(searches=items)
    gap_block = (
        "\n\n## Gaps the previous draft must address\n"
        + "\n".join(f"- {g}" for g in ev.gaps)
        if ev.gaps
        else ""
    )
    print("[Retry plan] replanning from evaluator gaps")
    return await run_planner(
        canonical_question + gap_block,
        DEFAULT_PHRASES_COUNT,
    )


def send_pushover_completion_notice() -> None:
    """Notify Pushover that a research job finished."""
    print("[Pushover] sending notification...")
    requests.post(
        PUSHOVER_MESSAGES_URL,
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "message": PUSHOVER_NOTIFY_MESSAGE,
        },
        timeout=30.0,
    ).raise_for_status()
    print("[Pushover] sent")


async def run_research(plan: SearchPlan) -> ResearchData:
    """Bounded tool loop (web_search only), then one structured `ResearchData` extraction."""
    print(f"[Research] agent run ({len(plan.searches)} planned searches)...")
    llm_tools = llm.bind_tools([web_search])
    messages: list[Any] = [
        SystemMessage(content=_research_instruction()),
        HumanMessage(content=f"# Search Topics\n{plan.model_dump_json()}"),
    ]
    for _ in range(MAX_RESEARCH_TURNS):
        ai = await llm_tools.ainvoke(messages)
        tool_calls = getattr(ai, "tool_calls", None)
        if not tool_calls:
            break
        messages.append(ai)
        for tc in tool_calls:
            messages.append(await _web_search_tool_message(tc))

    structured = llm.with_structured_output(ResearchData)
    final = await structured.ainvoke(
        messages
        + [
            HumanMessage(
                content="Output the final ResearchData for all searches above (structured)."
            )
        ]
    )
    print("[Research] done")
    return final


# Nodes
async def node_build_canonical(state: GraphState) -> dict[str, Any]:
    q = state["query"].strip()
    extra = (state.get("user_clarifications") or "").strip()
    if extra:
        canonical = q + "\n\n### User clarifications\n" + extra
    else:
        canonical = q
    return {"canonical": canonical}


async def node_triage(state: GraphState) -> dict[str, Any]:
    canonical = state["canonical"]
    t = await run_triage(canonical)
    return {"triage": t}


async def node_abort_triage(_state: GraphState) -> dict[str, Any]:
    print(
        "[Triage] abort - still ambiguous after max triage rounds; "
        "not starting planner/research."
    )
    return {"terminal_outcome": "triage_abort"}


async def node_clarify_draft(state: GraphState) -> dict[str, Any]:
    t = state["triage"]
    canonical = state["canonical"]
    q = await run_clarifier(canonical, t.what_is_ambiguous)
    print(f"--- Clarification question ---\n{q}\n")
    return {"pending_clarification_question": q}


async def node_clarify_ask(state: GraphState) -> dict[str, Any]:
    q = state["pending_clarification_question"]
    user_answer = interrupt({"question": q})
    if not isinstance(user_answer, str):
        user_answer = str(user_answer)
    block = f"\n\n### Clarification\n**Q:** {q}\n**A:** {user_answer}\n"
    uc = (state.get("user_clarifications") or "").strip()
    new_uc = (uc + block) if uc else block.strip()
    return {"user_clarifications": new_uc, "pending_clarification_question": ""}


async def node_plan(state: GraphState) -> dict[str, Any]:
    canonical = state["canonical"]
    ri = int(state.get("round_idx") or 0)
    if ri == 0:
        plan = await run_planner(canonical, DEFAULT_PHRASES_COUNT)
    else:
        ev = state["last_eval"]
        plan = await build_retry_search_plan(canonical, ev)
    return {"plan": plan}


async def node_research(state: GraphState) -> dict[str, Any]:
    plan = state["plan"]
    delta = await run_research(plan)
    return {"research_delta": delta}


async def node_merge(state: GraphState) -> dict[str, Any]:
    delta = state["research_delta"]
    acc = state.get("research_accum")
    if acc is None:
        return {"research_accum": delta}
    return {"research_accum": merge_research(acc, delta)}


async def node_report(state: GraphState) -> dict[str, Any]:
    canonical = state["canonical"]
    research = state["research_accum"]
    rep = await run_report(canonical, research)
    return {"report": rep}


async def node_evaluate(state: GraphState) -> dict[str, Any]:
    canonical = state["canonical"]
    research = state["research_accum"]
    report = state["report"]
    ev = await run_evaluator(canonical, report, research)
    return {"last_eval": ev}


async def node_success(_state: GraphState) -> dict[str, Any]:
    print("[Pipeline] evaluator approved - showing report")
    print("[Pipeline] done")
    return {"terminal_outcome": "success"}


async def node_fail_final(state: GraphState) -> dict[str, Any]:
    ev = state["last_eval"]
    print("[Evaluator] final fail - no retries left; showing last draft")
    print("[Evaluator] gaps:", ev.gaps)
    print("[Pipeline] stopped (evaluator never passed)")
    return {"terminal_outcome": "eval_fail"}


async def node_bump_round(state: GraphState) -> dict[str, Any]:
    print("[Pipeline] retrying with new searches...")
    ri = int(state.get("round_idx") or 0)
    return {"round_idx": ri + 1}



# Edges
def route_after_eval(state: GraphState) -> Literal["success", "fail_final", "retry"]:
    ev = state["last_eval"]
    ri = int(state.get("round_idx") or 0)
    if ev.passes:
        return "success"
    if ri >= MAX_EVALUATOR_RETRIES:
        return "fail_final"
    return "retry"

def route_after_triage(state: GraphState) -> Literal["abort_triage", "clarify", "plan"]:
    t = state["triage"]
    extra = state.get("user_clarifications") or ""
    n_clar = extra.count("### Clarification")
    if t.is_ambiguous:
        if n_clar >= MAX_TRIAGE_ROUNDS - 1:
            return "abort_triage"
        return "clarify"
    return "plan"


def build_graph(checkpointer: Any):
    g = StateGraph(GraphState)
    g.add_node("build_canonical", node_build_canonical)
    g.add_node("triage", node_triage)
    g.add_node("abort_triage", node_abort_triage)
    g.add_node("clarify_draft", node_clarify_draft)
    g.add_node("clarify_ask", node_clarify_ask)
    g.add_node("plan", node_plan)
    g.add_node("research", node_research)
    g.add_node("merge", node_merge)
    g.add_node("report", node_report)
    g.add_node("evaluate", node_evaluate)
    g.add_node("success", node_success)
    g.add_node("fail_final", node_fail_final)
    g.add_node("bump_round", node_bump_round)

    g.add_edge(START, "build_canonical")
    g.add_edge("build_canonical", "triage")
    g.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "abort_triage": "abort_triage",
            "clarify": "clarify_draft",
            "plan": "plan",
        },
    )
    g.add_edge("abort_triage", END)
    g.add_edge("clarify_draft", "clarify_ask")
    g.add_edge("clarify_ask", "build_canonical")
    g.add_edge("plan", "research")
    g.add_edge("research", "merge")
    g.add_edge("merge", "report")
    g.add_edge("report", "evaluate")
    g.add_conditional_edges(
        "evaluate",
        route_after_eval,
        {
            "success": "success",
            "fail_final": "fail_final",
            "retry": "bump_round",
        },
    )
    g.add_edge("success", END)
    g.add_edge("fail_final", END)
    g.add_edge("bump_round", "plan")

    return g.compile(checkpointer=checkpointer)


__all__ = [
    "MEMORY_DB_PATH",
    "GraphState",
    "Report",
    "EvaluationResult",
    "build_graph",
    "send_pushover_completion_notice",
]
