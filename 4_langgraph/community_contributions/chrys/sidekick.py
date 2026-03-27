"""Chrys sidekick: clarify → plan → worker/tools ↔ evaluator with SQLite checkpointing."""

import asyncio
import aiosqlite
import json
import os
import re
import uuid
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from pathlib import Path

from sidekick_tools import other_tools, playwright_tools

load_dotenv(override=True)

_CHRYS_DIR = Path(__file__).resolve().parent
DEFAULT_CHECKPOINT = str(_CHRYS_DIR / "sidekick_checkpoints.sqlite")
MAX_EVAL_LOOPS = int(os.getenv("SIDEKICK_MAX_EVAL_LOOPS", "8"))
# LangGraph default is 25; worker↔tools↔evaluator can exceed that in one user turn.
RECURSION_LIMIT = int(os.getenv("SIDEKICK_RECURSION_LIMIT", "100"))


class ClarificationOutput(BaseModel):
    ready_to_execute: bool = Field(
        description="True if the user request and success criteria are specific enough to start work"
    )
    questions: List[str] = Field(
        default_factory=list,
        description="2–4 short clarifying questions if not ready",
    )
    rationale: str = Field(default="", description="Brief reason for the decision")


class PlanOutput(BaseModel):
    steps: List[str] = Field(
        default_factory=list,
        description="3–5 concrete steps the worker should follow",
    )


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(
        description="Whether the success criteria have been met"
    )
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    skip_clarification: bool
    clarify_ready: bool
    evaluator_passes: int


def _msg_content(m: Any) -> str:
    if m is None:
        return ""
    if isinstance(m, dict):
        return str(m.get("content", ""))
    return str(getattr(m, "content", "") or "")


def _parse_json_dict_from_text(text: str) -> dict:
    """Extract a JSON object from model output (handles ```json fences)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("empty response")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        val = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise
        val = json.loads(text[start : end + 1])
    if not isinstance(val, dict):
        raise ValueError("JSON root must be an object")
    return val


def _default_router_output(model_cls: type[BaseModel]) -> BaseModel:
    if model_cls is ClarificationOutput:
        return ClarificationOutput(
            ready_to_execute=True,
            questions=[],
            rationale="",
        )
    if model_cls is PlanOutput:
        return PlanOutput(
            steps=[
                "Gather facts with search or Wikipedia if needed",
                "Use tools to complete the task",
                "Verify against success criteria",
            ]
        )
    if model_cls is EvaluatorOutput:
        return EvaluatorOutput(
            feedback="Evaluator could not parse model output; treating turn as complete.",
            success_criteria_met=True,
            user_input_needed=False,
        )
    raise ValueError(f"No default for {model_cls}")


class Sidekick:
    def __init__(self, thread_id: Optional[str] = None):
        self.worker_llm_with_tools = None
        self.llm_clarify = None
        self.llm_planner = None
        self.llm_evaluator = None
        self.tools = None
        self.graph = None
        self.sidekick_id = thread_id or str(uuid.uuid4())
        self.checkpointer: Optional[AsyncSqliteSaver] = None
        self.db_conn = None
        self.browser = None
        self.playwright = None

    def set_thread_id(self, thread_id: str) -> None:
        self.sidekick_id = thread_id.strip()

    def _invoke_router_output(
        self,
        llm: ChatOpenAI,
        model_cls: type[BaseModel],
        messages: List,
    ) -> BaseModel:
        """Structured output with JSON-in-text fallback (OpenRouter / some OSS models fail JSON schema mode)."""
        structured = llm.with_structured_output(model_cls)
        try:
            out = structured.invoke(messages)
            if isinstance(out, model_cls):
                return out
        except Exception:
            pass
        hints = {
            ClarificationOutput: '{"ready_to_execute": true, "questions": ["..."], "rationale": ""}',
            PlanOutput: '{"steps": ["step1", "step2"]}',
            EvaluatorOutput: (
                '{"feedback": "...", "success_criteria_met": true, "user_input_needed": false}'
            ),
        }
        hint = hints.get(model_cls, "{}")
        tail = HumanMessage(
            content=(
                "Reply with ONLY one JSON object matching this shape (no markdown, no prose):\n"
                f"{hint}"
            )
        )
        try:
            r = llm.invoke(messages + [tail])
            text = _msg_content(r)
            data = _parse_json_dict_from_text(text)
            return model_cls.model_validate(data)
        except Exception:
            return _default_router_output(model_cls)

    async def setup(self) -> None:
        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        model = "openai/gpt-oss-120b"
        base_url = "https://openrouter.ai/api/v1"
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        worker_llm = ChatOpenAI(model=model, temperature=0.2, base_url=base_url, api_key=openrouter_api_key)
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        # Plain LLMs: OpenRouter structured-output parsing can return invalid scalars; we use JSON fallback.
        self.llm_evaluator = ChatOpenAI(model=model, temperature=0, base_url=base_url, api_key=openrouter_api_key)
        self.llm_clarify = ChatOpenAI(model=model, temperature=0.1, base_url=base_url, api_key=openrouter_api_key)
        self.llm_planner = ChatOpenAI(model=model, temperature=0.2, base_url=base_url, api_key=openrouter_api_key)

        db_path = os.getenv("SIDEKICK_CHECKPOINT_DB", DEFAULT_CHECKPOINT)
        self.db_conn = await aiosqlite.connect(db_path)
        self.checkpointer = AsyncSqliteSaver(self.db_conn)
        await self.build_graph()

    def clarify(self, state: State) -> Dict[str, Any]:
        if state.get("skip_clarification"):
            return {"clarify_ready": True}

        crit = state.get("success_criteria") or "The answer should be clear and accurate"
        conv = self.format_conversation(state["messages"])
        prompt = f"""You decide whether there is enough context to execute the task with tools and research.

Success criteria:
{crit}

Conversation:
{conv}

If the request is vague, ambiguous, or missing constraints, set ready_to_execute false and provide 2–4 concise questions.
If you can proceed, set ready_to_execute true and use an empty questions list."""
        out = self._invoke_router_output(
            self.llm_clarify,
            ClarificationOutput,
            [HumanMessage(content=prompt)],
        )
        if out.ready_to_execute:
            return {"clarify_ready": True}
        qs = out.questions[:4] if out.questions else ["What is the exact scope you want?"]
        body = "Before I start, a few quick questions:\n\n" + "\n".join(
            f"{i + 1}. {q}" for i, q in enumerate(qs)
        )
        if out.rationale:
            body += f"\n\n({out.rationale.strip()})"
        return {
            "clarify_ready": False,
            "messages": [AIMessage(content=body)],
        }

    def clarify_router(self, state: State) -> str:
        if state.get("skip_clarification"):
            return "planner"
        if state.get("clarify_ready"):
            return "planner"
        return "END"

    def planner(self, state: State) -> Dict[str, Any]:
        crit = state.get("success_criteria") or "The answer should be clear and accurate"
        conv = self.format_conversation(state["messages"])
        prompt = f"""Given the conversation and success criteria, outline a short plan for the executing assistant.

Success criteria:
{crit}

Conversation:
{conv}

Return 3–5 concrete steps (action-oriented)."""
        plan = self._invoke_router_output(
            self.llm_planner,
            PlanOutput,
            [HumanMessage(content=prompt)],
        )
        steps = plan.steps[:5] if plan.steps else ["Gather facts with search or Wikipedia if needed", "Use tools to complete the task", "Verify against success criteria"]
        text = "**Plan**\n\n" + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps))
        return {"messages": [AIMessage(content=text)]}

    def worker(self, state: State) -> Dict[str, Any]:
        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You keep working until the success criteria is met or you need a clarification from the user.

Research: prefer the `search` tool, Wikipedia, or browser tools for factual or up-to-date information.
When you used tools for facts, end with a short **Sources** line listing what you relied on.

You have Python REPL — include print() to see output.
Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria:
{state["success_criteria"]}

Reply with a clear final answer, or ask a specific question prefixed with "Question:" if you must.
"""

        if state.get("feedback_on_work"):
            system_message += f"""
Your previous attempt did not meet the success criteria. Feedback:
{state["feedback_on_work"]}
Address this feedback and continue."""

        messages = state["messages"]
        found = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found = True
        if not found:
            messages = [SystemMessage(content=system_message)] + list(messages)

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool calls]"
                conversation += f"Assistant: {text}\n"
            elif isinstance(message, dict) and message.get("role") == "assistant":
                conversation += f"Assistant: {message.get('content', '')}\n"
        return conversation

    def evaluator(self, state: State) -> Dict[str, Any]:
        last_response = _msg_content(state["messages"][-1])
        eval_pass = state.get("evaluator_passes", 0) + 1

        system_message = """You evaluate whether the Assistant's last response satisfies the success criteria."""

        user_message = f"""Conversation:
{self.format_conversation(state["messages"])}

Success criteria:
{state["success_criteria"]}

Last assistant response to grade:
{last_response}

Decide feedback, success_criteria_met, and user_input_needed.
Give the Assistant benefit of the doubt if they used tools appropriately."""

        if state.get("feedback_on_work"):
            user_message += f"\nPrior feedback you gave: {state['feedback_on_work']}\nIf the Assistant repeats mistakes, set user_input_needed true."

        eval_result = self._invoke_router_output(
            self.llm_evaluator,
            EvaluatorOutput,
            [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message),
            ],
        )

        if (
            eval_pass >= MAX_EVAL_LOOPS
            and not eval_result.success_criteria_met
            and not eval_result.user_input_needed
        ):
            eval_result = EvaluatorOutput(
                feedback=f"Stopped after {MAX_EVAL_LOOPS} evaluation loops. Last feedback: {eval_result.feedback}",
                success_criteria_met=True,
                user_input_needed=False,
            )

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
            "evaluator_passes": eval_pass,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"

    async def build_graph(self) -> None:
        graph_builder = StateGraph(State)
        graph_builder.add_node("clarify", self.clarify)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "clarify")
        graph_builder.add_conditional_edges(
            "clarify",
            self.clarify_router,
            {"planner": "planner", "END": END},
        )
        graph_builder.add_edge("planner", "worker")
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

        assert self.checkpointer is not None
        self.graph = graph_builder.compile(checkpointer=self.checkpointer)

    @staticmethod
    def trace_from_messages(msgs: List[Any]) -> str:
        lines: List[str] = []
        for m in msgs:
            tcs = getattr(m, "tool_calls", None) or []
            for tc in tcs:
                name = tc.get("name", "?") if isinstance(tc, dict) else getattr(tc, "name", "?")
                lines.append(str(name))
        return "\n".join(lines[-40:]) if lines else "(no tool calls this turn)"

    @staticmethod
    def _slice_after_last_user(msgs: List[Any], user_text: str) -> List[Any]:
        idx = None
        for i in range(len(msgs) - 1, -1, -1):
            m = msgs[i]
            if isinstance(m, HumanMessage) and (m.content or "").strip() == (user_text or "").strip():
                idx = i
                break
        if idx is None:
            return msgs
        return msgs[idx + 1 :]

    def extract_gradio_turn(self, result: Dict[str, Any], user_text: str) -> List[Dict[str, str]]:
        """User bubble plus every assistant message produced after this user send (plan, worker, evaluator)."""
        msgs = result["messages"]
        out: List[Dict[str, str]] = [{"role": "user", "content": user_text}]
        tail = self._slice_after_last_user(msgs, user_text)
        for m in tail:
            if isinstance(m, AIMessage):
                c = _msg_content(m)
                if c.strip():
                    out.append({"role": "assistant", "content": c})
            elif isinstance(m, dict) and m.get("role") == "assistant":
                c = _msg_content(m)
                if c.strip():
                    out.append({"role": "assistant", "content": c})
        return out

    async def run_superstep(
        self,
        message: str,
        success_criteria: str,
        history: List[Dict[str, str]],
        skip_clarification: bool = False,
    ):
        config: Dict[str, Any] = {
            "configurable": {"thread_id": self.sidekick_id},
            "recursion_limit": RECURSION_LIMIT,
        }
        state: Dict[str, Any] = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria
            or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "skip_clarification": skip_clarification,
            "evaluator_passes": 0,
            "clarify_ready": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        turn_msgs = self._slice_after_last_user(result["messages"], message)
        trace = self.trace_from_messages(turn_msgs)
        new_entries = self.extract_gradio_turn(result, message)
        return history + new_entries, trace

    async def _close_async(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.db_conn is not None:
            await self.db_conn.close()

    def cleanup(self) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._close_async())
        except RuntimeError:
            asyncio.run(self._close_async())
