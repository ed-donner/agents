"""
Week 4 pattern: worker → (tools | evaluator) → conditional loop until done.

Same topology as the course Sidekick lab, tailored for platform / SRE incident
triage. The evaluator uses structured output (Pydantic) to decide whether the
worker satisfied the user’s success criteria.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Optional
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- Tools (read-only; merged here to keep the contribution folder ≤5 files) ---

_DOMAINS = frozenset({"kubernetes", "network", "database", "generic"})


@tool
def incident_clock_utc() -> str:
    """Current time in ISO 8601 UTC. Use for correlation windows and narrative timelines."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@tool
def suggest_severity_from_text(incident_snippet: str) -> str:
    """
    Rough severity hint from keywords in an alert, ticket, or log paste.
    This is a heuristic only—not a replacement for your official severity model.
    """
    text = incident_snippet.lower()
    if any(k in text for k in ("sev0", "complete outage", "data loss", "breach", "p1")):
        return "Hint: treat as P1 / major until disproven—page incident lead and stabilize first."
    if any(k in text for k in ("many pods", "latency", "5xx", "503", "slow", "timeouts")):
        return "Hint: likely P2—significant impact; staffed response and clear comms cadence."
    if any(k in text for k in ("flap", "intermittent", "single pod", "noisy")):
        return "Hint: often P3—confirm blast radius; rule out noise before deep dives."
    return "Hint: severity unclear—gather scope, start time, and what changed before labeling."


@tool
def runbook_outline(domain: str) -> str:
    """
    Short checklist-style outline for a common platform domain.

    Args:
        domain: One of: kubernetes, network, database, generic.
    """
    key = domain.strip().lower()
    if key not in _DOMAINS:
        key = "generic"

    outlines = {
        "kubernetes": """Kubernetes — stabilize fast
• Blast radius: namespaces, workloads, node conditions, recent deploys.
• Events: describe pod, deployment rollout, image pull and quota errors.
• Mitigate: rollback, scale, PDB-aware restarts; capture timelines.""",
        "network": """Network — prove the path
• Edge → ingress → service → pod; DNS, TLS, LB health checks.
• Recent changes: firewall rules, service mesh routes, certificates.
• Evidence: only gather traces/pcaps if policy allows.""",
        "database": """Database — protect data first
• Replication lag, connections, locks, slow queries; backup posture.
• Schema or migration timeline; failover only per approved runbook.
• Communicate RPO/RTO expectations with stakeholders.""",
        "generic": """Generic incident — structure
• Impact, detection source, customer blast radius, start time.
• Change ledger: deploys, config, traffic shifts.
• Stabilize before root cause; status updates on your org’s cadence.""",
    }
    return outlines[key]


def all_tools():
    return [incident_clock_utc, suggest_severity_from_text, runbook_outline]


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


def _format_conversation(messages: List[Any]) -> str:
    lines: List[str] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            lines.append(f"User: {m.content}")
        elif isinstance(m, AIMessage):
            text = m.content or "[tool calls]"
            lines.append(f"Assistant: {text}")
    return "\n".join(lines) if lines else "(empty)"


class PlatformIncidentCopilot:
    """
    Incident triage copilot: worker with tools, then an evaluator that can send
    the worker back for another pass until criteria are met or user input is required.
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        self._tools = all_tools()
        worker_llm = ChatOpenAI(model=model)
        self._worker_llm = worker_llm.bind_tools(self._tools)
        evaluator_llm = ChatOpenAI(model=model)
        self._evaluator_structured = evaluator_llm.with_structured_output(EvaluatorOutput)
        self._memory = MemorySaver()
        self._graph = self._compile()

    def _worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a senior platform / SRE engineer helping triage production incidents.

You may call tools for UTC time, keyword-based severity hints, and short runbook outlines. Tools never touch real infrastructure—phrase recommendations as actions for the operator.

Style:
• Prefer short sections: situation, hypotheses, next checks, comms / escalation.
• Do not claim you ran kubectl, SSH, or cloud APIs—suggest commands or checks instead.
• If you need facts (region, service, timeline), ask one sharp question starting with "Question:".

Success criteria for this turn:
{state["success_criteria"]}
"""

        if state.get("feedback_on_work"):
            system_message += f"""
Your last answer did not meet the success criteria. Evaluator feedback:
{state["feedback_on_work"]}
Improve the response or ask a focused clarifying question."""

        messages = list(state["messages"])
        updated_system = False
        for m in messages:
            if isinstance(m, SystemMessage):
                m.content = system_message
                updated_system = True
                break
        if not updated_system:
            messages = [SystemMessage(content=system_message)] + messages

        response = self._worker_llm.invoke(messages)
        return {"messages": [response]}

    @staticmethod
    def _worker_router(state: State) -> str:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return "evaluator"

    def _evaluator_node(self, state: State) -> Dict[str, Any]:
        last = state["messages"][-1]
        last_text = getattr(last, "content", None) or ""

        system_message = """You evaluate responses from a senior platform engineer assistant.
Accept answers that are practical, safety-aware, and aligned with the success criteria.
Send the worker back only if the answer is vague, unsafe, or misses required elements."""

        user_message = f"""Full conversation:
{_format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Latest assistant message (to judge):
{last_text}
"""
        if state.get("feedback_on_work"):
            user_message += (
                f"\nEarlier evaluator note (avoid repeating the same gap): {state['feedback_on_work']}\n"
            )

        result = self._evaluator_structured.invoke(
            [SystemMessage(content=system_message), HumanMessage(content=user_message)]
        )
        return {
            "messages": [AIMessage(content=f"Evaluator feedback: {result.feedback}")],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
        }

    @staticmethod
    def _route_after_eval(state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    def _compile(self):
        builder = StateGraph(State)
        builder.add_node("worker", self._worker)
        builder.add_node("tools", ToolNode(tools=self._tools))
        builder.add_node("evaluator", self._evaluator_node)

        builder.add_conditional_edges(
            "worker",
            self._worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        builder.add_edge("tools", "worker")
        builder.add_conditional_edges(
            "evaluator",
            self._route_after_eval,
            {"worker": "worker", "END": END},
        )
        builder.add_edge(START, "worker")
        return builder.compile(checkpointer=self._memory)

    async def arun_turn(self, user_text: str, success_criteria: str, thread_id: str) -> Dict[str, Any]:
        """Run one user message through the graph until the evaluator ends the loop."""
        config = {"configurable": {"thread_id": thread_id}}
        criteria = (success_criteria or "").strip() or (
            "Include triage summary, likely causes, concrete validation steps, and when to escalate."
        )
        payload = {
            "messages": [HumanMessage(content=user_text.strip())],
            "success_criteria": criteria,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        return await self._graph.ainvoke(payload, config=config)


def new_thread_id() -> str:
    """Fresh conversation + checkpoint namespace for Gradio reset."""
    return str(uuid4())
