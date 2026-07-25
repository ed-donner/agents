from __future__ import annotations

import asyncio
import uuid
from contextlib import AsyncExitStack
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from job_hunt_tools import SANDBOX_ROOT, build_core_tools, playwright_browser_tools

load_dotenv(override=True)


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description=(
            "True if more input is needed from the user, clarifications, or the assistant is stuck"
        )
    )


class JobHuntAssistant:
    """Sidekick-style agent specialized for job search, research, and application drafts."""

    def __init__(self) -> None:
        self.worker_llm_with_tools: Optional[Any] = None
        self.evaluator_llm_with_output: Optional[Any] = None
        self.tools: List[Any] = []
        self.graph: Optional[Any] = None
        self.thread_id: str = str(uuid.uuid4())
        self.browser: Any = None
        self.playwright: Any = None
        self._checkpoint_stack: Optional[AsyncExitStack] = None

    async def setup(self) -> None:
        SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
        db_path = SANDBOX_ROOT / "job_hunt_checkpoints.db"
        # SqliteSaver is sync-only; ainvoke() needs AsyncSqliteSaver (see langgraph checkpoint docs).
        self._checkpoint_stack = AsyncExitStack()
        checkpointer = await self._checkpoint_stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string(str(db_path.resolve()))
        )

        core = build_core_tools()
        pw_tools, self.browser, self.playwright = await playwright_browser_tools()
        self.tools = core + list(pw_tools)

        worker_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        evaluator_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)

        graph_builder = StateGraph(State)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_conditional_edges(
            "worker",
            self.worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self.route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )
        graph_builder.add_edge(START, "worker")

        self.graph = graph_builder.compile(checkpointer=checkpointer)

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are an expert job-hunt copilot. Help the user research roles, understand companies,
tailor materials, and prepare outreach — using tools when facts must be grounded.

Rules:
- Never invent salary numbers, exact benefits, application deadlines, or job requirements. If unknown, say so and suggest how to verify (official posting, recruiter, etc.).
- If the user named a JD link, prefer fetch_job_page_text before guessing requirements.
- Prefer search_web for fresh postings and news (uses DuckDuckGo without any API key; optional SERPER_API_KEY for Google). Also use wikipedia_lookup and fetch_job_page_text with user-supplied URLs.
- When you produce a deliverable the user can reuse (JD summary, keyword map, cover letter draft, outreach email), call save_job_application_package.
- If the user asks to be notified on their phone/desktop, or success criteria mention alerting them when done, call send_push_notification with a short summary (after completing the work, unless they only wanted a ping). Requires Pushover env vars.
- Browser tools (if available): navigate and extract text from pages when fetch_job_page_text is not enough (e.g. heavy JavaScript sites).
- Ask a clear question only when you truly need missing info (current location, seniority, URL, etc.). Start questions with "Question:".

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria (must be satisfied before the run is accepted):
{state["success_criteria"]}
"""

        if state.get("feedback_on_work"):
            system_message += f"""
The previous answer did not meet the success criteria. Evaluator feedback:
{state["feedback_on_work"]}
Revise using tools if needed, or ask the user a concrete question."""

        messages = state["messages"]
        found_system = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system = True

        if not found_system:
            messages = [SystemMessage(content=system_message)] + list(messages)

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "evaluator"

    @staticmethod
    def format_conversation(messages: List[Any]) -> str:
        lines: List[str] = []
        for message in messages:
            if isinstance(message, HumanMessage):
                lines.append(f"User: {message.content}")
            elif isinstance(message, AIMessage):
                text = message.content or "[tool calls]"
                lines.append(f"Assistant: {text}")
        lines.append("")
        return "\n".join(lines)

    def evaluator(self, state: State) -> Dict[str, Any]:
        last = state["messages"][-1]
        last_response = last.content if hasattr(last, "content") else str(last)

        system_message = """You evaluate a Job Hunt Assistant. Decide if the assistant's last reply meets the success criteria,
and whether the user must supply more information. Be strict about fabricated company/job facts."""

        user_message = f"""Conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Final assistant reply to judge:
{last_response}

If the assistant claims to have saved a file via save_job_application_package, assume the tool succeeded unless the reply is inconsistent.
If they say they sent a Pushover notification, assume send_push_notification succeeded unless the reply contradicts the tool result.
Reject if salary/benefits/deadlines are stated without a clear source from search, fetched page, or user message.
"""

        if state.get("feedback_on_work"):
            user_message += (
                f"\nPrior evaluator feedback (avoid repeat failure): {state['feedback_on_work']}\n"
                "If the assistant repeats errors, set user_input_needed true."
            )

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def run_superstep(
        self,
        user_text: str,
        success_criteria: str,
        history: Optional[List[dict]],
    ) -> List[dict]:
        if history is None:
            history = []

        cfg = {"configurable": {"thread_id": self.thread_id}}
        state: State = {
            "messages": [HumanMessage(content=user_text)],
            "success_criteria": success_criteria
            or "Reply is actionable, accurate, and does not invent job facts.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }

        result = await self.graph.ainvoke(state, config=cfg)
        msgs = result["messages"]
        assistant_reply = msgs[-2] if len(msgs) >= 2 else msgs[-1]
        eval_msg = msgs[-1]

        def _content(m: Any) -> str:
            if hasattr(m, "content"):
                return m.content or ""
            if isinstance(m, dict):
                return str(m.get("content", m))
            return str(m)

        user_msg = {"role": "user", "content": user_text}
        assistant_out = {"role": "assistant", "content": _content(assistant_reply)}
        feedback_out = {"role": "assistant", "content": _content(eval_msg)}
        return history + [user_msg, assistant_out, feedback_out]

    def cleanup(self) -> None:
        async def _close() -> None:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self._checkpoint_stack:
                await self._checkpoint_stack.aclose()
                self._checkpoint_stack = None

        if self.browser or self.playwright or self._checkpoint_stack:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_close())
            except RuntimeError:
                asyncio.run(_close())
