"""LangGraph Career Sprint: worker, tools, evaluator loop with SQLite checkpointing."""

from __future__ import annotations

import os
import sys
import uuid

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

import aiosqlite
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from tools import build_tools

load_dotenv(override=True)

# Stop worker↔evaluator loops when the rubric never flips to "done" or "needs user".
MAX_EVAL_ROUNDS = 8
# Stop worker↔tools loops: each tool batch counts as one round (eval_rounds does not).
MAX_TOOL_ROUNDS = 40

DEFAULT_SPRINT_CRITERIA = """\
The sprint is complete when the answer:
1) Names the target company and role explicitly.
2) Cites at least two distinct sources for factual company or role claims (URLs or publication names).
3) Gives interview talking points as a bullet list AND one short outreach or follow-up paragraph.
4) References read_career_profile if me/summary.txt exists, or states that no profile was available.
5) Names the Markdown file written under sandbox/ containing the sprint pack (or explains why file write was skipped).
"""


class SprintRubricAssessment(BaseModel):
    """Structured evaluator output (same decision shape as the course lab, career-specific copy)."""

    feedback: str = Field(
        description="Concrete feedback on whether the sprint deliverable meets the rubric and what is missing."
    )
    success_criteria_met: bool = Field(
        description="True only if the assistant's last message satisfies the sprint success criteria."
    )
    user_input_needed: bool = Field(
        description=(
            "True if the user must reply (clarifying question, missing company/role, or blocked without input)."
        ),
    )


class CareerSprintState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    eval_rounds: int
    tool_rounds: int
    company_name: Optional[str]
    role_title: Optional[str]


def _checkpoint_path() -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "checkpoints")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "career_sprint.db")


class CareerSprintGraph:
    """Stateful LangGraph application: research + draft + rubric loop."""

    def __init__(self) -> None:
        self.worker_llm_with_tools = None
        self.evaluator_llm = None
        self.tools: List[Any] = []
        self.graph = None
        self.memory: Optional[AsyncSqliteSaver] = None
        self._db_conn = None

    async def setup(self) -> None:
        self._db_conn = await aiosqlite.connect(_checkpoint_path())
        await self._db_conn.execute("PRAGMA journal_mode=WAL;")
        await self._db_conn.commit()
        self.memory = AsyncSqliteSaver(self._db_conn)

        self.tools = build_tools()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        worker = ChatOpenAI(model=model, temperature=0.2)
        self.worker_llm_with_tools = worker.bind_tools(self.tools)
        evaluator = ChatOpenAI(model=model, temperature=0)
        self.evaluator_llm = evaluator.with_structured_output(SprintRubricAssessment)
        await self._build_graph()

    def _sprint_context(self, state: CareerSprintState) -> str:
        parts = []
        if state.get("company_name"):
            parts.append(f"Target company: {state['company_name']}")
        if state.get("role_title"):
            parts.append(f"Target role: {state['role_title']}")
        return "\n".join(parts) if parts else "No company/role fields provided; infer from the user or ask."

    def worker(self, state: CareerSprintState) -> Dict[str, Any]:
        sprint_block = self._sprint_context(state)
        system_message = f"""You are a career sprint coach for one focused session. You help the user prepare for a specific company + role using tools.

Use web_search for fresh facts. Use read_career_profile to align tone with their local bio (me/summary.txt) when present.
Use file tools only inside the sandbox/ folder; write a concise Markdown "sprint pack" with sections: Snapshot, Sources, Talking points, Outreach draft.
You may use Wikipedia for general background. Python REPL is for tiny calculations or formatting only - never for secrets.

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{sprint_block}

Success criteria for this sprint:
{state["success_criteria"]}

Reply with either:
- A clear Question: ... if you need clarification, OR
- Your final answer when the sprint deliverable is ready (no question).

If you previously received evaluator feedback, incorporate it before finishing.
"""

        if state.get("feedback_on_work"):
            system_message += f"""

Previous rubric feedback (address this before claiming done):
{state["feedback_on_work"]}
"""

        messages: List[BaseMessage] = list(state["messages"])
        found = False
        for m in messages:
            if isinstance(m, SystemMessage):
                m.content = system_message
                found = True
                break
        if not found:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def after_tools(self, state: CareerSprintState) -> Dict[str, Any]:
        return {"tool_rounds": state.get("tool_rounds", 0) + 1}

    def worker_router(self, state: CareerSprintState) -> str:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            if state.get("tool_rounds", 0) >= MAX_TOOL_ROUNDS:
                return "evaluator"
            return "tools"
        return "evaluator"

    def _format_thread(self, messages: List[BaseMessage]) -> str:
        lines: List[str] = []
        for m in messages:
            if isinstance(m, HumanMessage):
                lines.append(f"User: {m.content}")
            elif isinstance(m, AIMessage):
                text = m.content or "[tool calls]"
                lines.append(f"Assistant: {text}")
        return "\n".join(lines)

    def evaluator(self, state: CareerSprintState) -> Dict[str, Any]:
        last = state["messages"][-1]
        last_text = (last.content or "").strip()
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None) and not last_text:
            last_text = (
                "[Assistant requested more tool calls; maximum tool rounds for this turn "
                "were reached before a final text answer.]"
            )

        rubric_user = f"""Evaluate the last assistant message for a career sprint.

Thread so far:
{self._format_thread(state["messages"])}

Sprint success criteria:
{state["success_criteria"]}

Company/role hints:
{self._sprint_context(state)}

Last assistant message to score:
{last_text}

Rules:
- If the assistant asked a Question: or needs missing info, set user_input_needed true and success_criteria_met false unless the question itself satisfies the user.
- If the assistant claims a file was written under sandbox/, assume tools could do so unless obviously inconsistent.
- Require evidence of two distinct sources when criteria ask for citations.

Return structured rubric fields only.
"""

        system_msg = SystemMessage(
            content=(
                "You are an independent sprint rubric grader. "
                "Be strict on citations and deliverable shape; be fair on tool use."
            )
        )
        human = HumanMessage(content=rubric_user)
        result: SprintRubricAssessment = self.evaluator_llm.invoke([system_msg, human])

        rounds = state.get("eval_rounds", 0) + 1
        note = f"Sprint rubric: {result.feedback}"
        if rounds >= MAX_EVAL_ROUNDS and not (
            result.success_criteria_met or result.user_input_needed
        ):
            note += (
                "\n\n_(Maximum automated revision rounds reached; "
                "review the rubric feedback and continue in your next message if needed.)_"
            )
        return {
            "messages": [AIMessage(content=note)],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
            "eval_rounds": rounds,
        }

    def route_after_eval(self, state: CareerSprintState) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        if state.get("eval_rounds", 0) >= MAX_EVAL_ROUNDS:
            return "END"
        return "worker"

    async def _build_graph(self) -> None:
        gb = StateGraph(CareerSprintState)
        gb.add_node("worker", self.worker)
        gb.add_node("tools", ToolNode(tools=self.tools))
        gb.add_node("after_tools", self.after_tools)
        gb.add_node("evaluator", self.evaluator)
        gb.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        gb.add_edge("tools", "after_tools")
        gb.add_edge("after_tools", "worker")
        gb.add_conditional_edges(
            "evaluator",
            self.route_after_eval,
            {"worker": "worker", "END": END},
        )
        gb.add_edge(START, "worker")
        self.graph = gb.compile(checkpointer=self.memory)

    async def run_turn(
        self,
        user_text: str,
        success_criteria: str,
        company: str,
        role: str,
        prior_messages: List[BaseMessage],
        thread_id: str,
    ) -> Dict[str, Any]:
        """Single user turn: full message list + fresh feedback flags (course-style full-state invoke)."""
        if self.graph is None:
            raise RuntimeError("Call await setup() first")

        msgs: List[BaseMessage] = list(prior_messages)
        msgs.append(HumanMessage(content=user_text))

        state: CareerSprintState = {
            "messages": msgs,
            "success_criteria": (success_criteria or "").strip() or DEFAULT_SPRINT_CRITERIA,
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "eval_rounds": 0,
            "tool_rounds": 0,
            "company_name": company.strip() or None,
            "role_title": role.strip() or None,
        }

        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 500,
        }
        return await self.graph.ainvoke(state, config=config)

    async def aclose(self) -> None:
        if self._db_conn is not None:
            await self._db_conn.close()
            self._db_conn = None


def new_thread_id() -> str:
    return str(uuid.uuid4())
