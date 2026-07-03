"""
LangGraph workflow: small-talk routing → clarifier → planning → web search (tool) → evaluator.

Uses ``generic_llm`` for classification, small talk, clarification, planning, search (tool-calling + synthesis),
and ``evaluation_llm`` for the evaluator. Web results come from DuckDuckGo via LangChain's
``DuckDuckGoSearchResults`` (install the ``ddgs`` package: ``pip install ddgs``).
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# --- Web search (DuckDuckGo via LangChain) ---

search_engine_tool = DuckDuckGoSearchResults(
    num_results=5,
    name="internet_search",
    description="Search the public web for current information. Pass a short, focused query string.",
)

SEARCH_TOOLS = [search_engine_tool]
tool_node = ToolNode(SEARCH_TOOLS)

generic_llm = ChatOpenAI(model="gpt-4o-mini")
evaluation_llm = ChatOpenAI(model="gpt-4o-mini")

search_llm = generic_llm.bind_tools(SEARCH_TOOLS)


class SmallTalkClassification(BaseModel):
    is_small_talk: bool = Field(
        description=(
            "True ONLY for pure social pleasantries with no information or research ask "
            "(e.g. hi, thanks, bye, how are you, emoji-only). "
            "False for any question, factual request, instruction to search/look up/explain, "
            "or a mix of chit-chat plus a real request (treat as not small talk)."
        )
    )


class ClarifierDecision(BaseModel):
    needs_clarification: bool = Field(
        description=(
            "True if the user's request is too vague, ambiguous, or missing key details "
            "to run a web search or answer well without guessing."
        )
    )
    clarifying_question: Optional[str] = Field(
        default=None,
        description="One short, specific question to ask the user; set when needs_clarification is True.",
    )


class EvaluationDecision(BaseModel):
    answer_is_adequate: bool = Field(
        description="True if the assistant's last answer addresses the user's request well enough to finish."
    )


class ResearchPlan(BaseModel):
    intent_summary: str = Field(
        description="One sentence describing what a successful answer must cover."
    )
    steps: list[str] = Field(
        description=(
            "3–6 concrete, ordered steps (e.g. clarify scope, run a targeted search, verify facts, synthesize)."
        ),
        min_length=1,
    )


_llm_classify_small_talk = generic_llm.with_structured_output(SmallTalkClassification)
_llm_clarifier = generic_llm.with_structured_output(ClarifierDecision)
_planner_structured = generic_llm.with_structured_output(ResearchPlan)
_evaluator_structured = evaluation_llm.with_structured_output(EvaluationDecision)


SEARCH_SYSTEM_PROMPT = """You are a research assistant with access to web search.
When the user needs up-to-date or factual information from the internet, call the `internet_search` tool once with a short, focused query (keywords, not a full essay).
If the user's request can be answered without searching, reply directly in plain text without calling tools."""

SYNTHESIS_SYSTEM_PROMPT = """You are a research assistant. You have received web search result snippets for the user's question.
Write a clear, helpful answer grounded in those results. Mention uncertainty if snippets are thin or contradictory.
If results are missing or irrelevant, say so briefly and answer from general knowledge only what you can justify."""


# --- State ---


class WorkflowState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    is_small_talk: Optional[bool]
    needs_clarification: Optional[bool]
    research_plan: Optional[str]
    evaluation_passed: Optional[bool]


def _message_text_content(msg: BaseMessage) -> str:
    """Normalize LangChain message content (str or multimodal list) to plain text."""
    c = getattr(msg, "content", None)
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        parts: list[str] = []
        for block in c:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif isinstance(block, str):
                parts.append(block)
            else:
                parts.append(str(block))
        return " ".join(parts).strip()
    return (str(c) if c is not None else "").strip()


def _last_user_text(state: WorkflowState) -> str:
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            t = _message_text_content(m)
            if t:
                return t
    return ""


def _user_assistant_turns(state: WorkflowState) -> list[BaseMessage]:
    """State messages as alternating user/assistant chat turns (no tool payloads)."""
    out: list[BaseMessage] = []
    for m in state["messages"]:
        if isinstance(m, HumanMessage):
            t = _message_text_content(m)
            if t:
                out.append(HumanMessage(content=t))
        elif isinstance(m, AIMessage):
            text = (m.content or "").strip()
            if not text and m.tool_calls:
                text = "[Assistant invoked tools]"
            out.append(AIMessage(content=text))
    return out


# --- 1) Small-talk classifier ---


def classify_small_talk(state: WorkflowState) -> dict[str, Any]:
    user_text = _last_user_text(state)
    if not user_text:
        # No usable user text: skip small-talk branch so clarifier / planner can react.
        return {"is_small_talk": False}
    convo = _user_assistant_turns(state)
    if not convo:
        return {"is_small_talk": False}
    result = _llm_classify_small_talk.invoke(
        [
            SystemMessage(
                content=(
                    "You route the **latest user message** (most recent Human turn) using the full "
                    "conversation as context.\n\n"
                    "Set is_small_talk=True **only** when the latest user message is purely social "
                    "pleasantries with **no** request for facts, search, research, explanations, or tasks "
                    "(e.g. hello, thanks, goodbye, how are you, casual weather chat with no ask).\n\n"
                    "Set is_small_talk=False when there is **any** substantive ask: questions (including "
                    "\"how are you\" mixed with a real question), topics to look up, instructions, "
                    "or ambiguity that needs clarification — default to False when unsure."
                )
            ),
            *convo,
        ]
    )
    return {"is_small_talk": result.is_small_talk}


def route_after_small_talk(
    state: WorkflowState,
) -> Literal["handle_small_talk", "clarifying_agent"]:
    if state.get("is_small_talk"):
        return "handle_small_talk"
    return "clarifying_agent"


# --- Small-talk branch ---


def handle_small_talk(state: WorkflowState) -> dict[str, Any]:
    user_text = _last_user_text(state)
    convo = _user_assistant_turns(state)
    if not convo:
        convo = [HumanMessage(content=user_text or "Hello")]
    reply = generic_llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a brief, friendly assistant. The user is making small talk. "
                    "Use the conversation history for continuity. "
                    "Respond warmly in one or two short sentences to their latest message. If appropriate, gently "
                    "invite them to ask a question you could help research on the web."
                )
            ),
            *convo,
        ]
    )
    return {"messages": [AIMessage(content=reply.content or "")]}


# --- 2) Clarifying questions ---


def clarifying_agent(state: WorkflowState) -> dict[str, Any]:
    user_text = _last_user_text(state)
    if not user_text:
        return {
            "needs_clarification": True,
            "messages": [
                AIMessage(content="What would you like me to look up or help you with?")
            ],
        }

    convo = _user_assistant_turns(state)
    if not convo:
        convo = [HumanMessage(content=user_text)]

    decision = _llm_clarifier.invoke(
        [
            SystemMessage(
                content=(
                    "You triage user requests before a web search. You see the conversation as user and "
                    "assistant messages. Focus on the **latest user message** in light of any prior context. "
                    "Decide if it is clear enough to search without guessing (topic, intent, and any constraints "
                    "like time or region). If clarification is needed, set needs_clarification true and provide "
                    "one concise question."
                )
            ),
            *convo,
        ]
    )

    if decision.needs_clarification:
        question = (decision.clarifying_question or "").strip() or (
            "Could you share a bit more detail about what you want to find out?"
        )
        return {"needs_clarification": True, "messages": [AIMessage(content=question)]}

    return {"needs_clarification": False, "messages": []}


def route_after_clarifier(state: WorkflowState) -> Literal["planning_agent", END]:
    if state.get("needs_clarification"):
        return END
    return "planning_agent"


# --- 3) Planning agent (structured plan before search) ---


def planning_agent(state: WorkflowState) -> dict[str, Any]:
    convo = _user_assistant_turns(state)
    if not convo:
        return {
            "research_plan": "Answer the user's question directly or with one web search.",
            "messages": [],
        }

    plan = _planner_structured.invoke(
        [
            SystemMessage(
                content=(
                    "You are a planning agent before web research. Given the user/assistant conversation, "
                    "produce a short intent summary and ordered steps. Steps should be actionable for a researcher "
                    "with `internet_search` (e.g. draft query angles, what to verify, how to structure the final answer). "
                    "Keep steps concise."
                )
            ),
            *convo,
        ]
    )
    lines = [f"Goal: {plan.intent_summary.strip()}"] + [
        f"{i}. {s.strip()}" for i, s in enumerate(plan.steps, start=1)
    ]
    plan_text = "\n".join(lines)
    # Plan is shown in the Gradio side panel; keep it out of chat messages (still in state for search_agent).
    return {"research_plan": plan_text, "messages": []}


# --- 4) Search agent (LLM + internet_search tool, then synthesis) ---


def _plan_system_suffix(state: WorkflowState) -> str:
    plan = (state.get("research_plan") or "").strip()
    if not plan:
        return ""
    return (
        "\n\nUse this plan as your guide (adapt if search results require it):\n"
        f"{plan}\n"
    )


def search_agent(state: WorkflowState) -> dict[str, Any]:
    messages = list(state["messages"])
    last = messages[-1] if messages else None
    plan_suffix = _plan_system_suffix(state)

    if isinstance(last, ToolMessage):
        syn_prompt = SYNTHESIS_SYSTEM_PROMPT + plan_suffix
        reply = generic_llm.invoke([SystemMessage(content=syn_prompt)] + messages)
        return {"messages": [AIMessage(content=reply.content or "")]}

    search_prompt = SEARCH_SYSTEM_PROMPT + plan_suffix
    reply = search_llm.invoke([SystemMessage(content=search_prompt)] + messages)
    return {"messages": [reply]}


def route_after_search_agent(state: WorkflowState) -> Literal["tools", "evaluator"]:
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "evaluator"


# --- 5) Evaluator (structured LLM) ---


def evaluator_agent(state: WorkflowState) -> dict[str, Any]:
    convo = _user_assistant_turns(state)
    if not any(isinstance(m, AIMessage) and (m.content or "").strip() for m in convo):
        return {"evaluation_passed": False}

    verdict = _evaluator_structured.invoke(
        [
            SystemMessage(
                content=(
                    "You see the conversation as user and assistant messages. "
                    "Judge whether the assistant's **latest** reply adequately addresses the user's request "
                    "for this turn, using earlier turns only as needed for context. "
                    "Be fair: minor style issues should still pass if the substance is there."
                )
            ),
            *convo,
        ]
    )
    return {"evaluation_passed": verdict.answer_is_adequate}


def route_after_evaluator(state: WorkflowState) -> Literal["search_agent", END]:
    if state.get("evaluation_passed"):
        return END
    # Retry search path once with a nudge (placeholder)
    return "search_agent"


def build_graph():
    g = StateGraph(WorkflowState)

    g.add_node("classify_small_talk", classify_small_talk)
    g.add_node("handle_small_talk", handle_small_talk)
    g.add_node("clarifying_agent", clarifying_agent)
    g.add_node("planning_agent", planning_agent)
    g.add_node("search_agent", search_agent)
    g.add_node("tools", tool_node)
    g.add_node("evaluator", evaluator_agent)

    g.add_edge(START, "classify_small_talk")
    g.add_conditional_edges(
        "classify_small_talk",
        route_after_small_talk,
        {"handle_small_talk": "handle_small_talk", "clarifying_agent": "clarifying_agent"},
    )
    g.add_edge("handle_small_talk", END)

    g.add_conditional_edges(
        "clarifying_agent",
        route_after_clarifier,
        {"planning_agent": "planning_agent", END: END},
    )
    g.add_edge("planning_agent", "search_agent")

    g.add_conditional_edges(
        "search_agent",
        route_after_search_agent,
        {"tools": "tools", "evaluator": "evaluator"},
    )
    g.add_edge("tools", "search_agent")

    g.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {"search_agent": "search_agent", END: END},
    )

    return g.compile(checkpointer=MemorySaver())


graph = build_graph()
