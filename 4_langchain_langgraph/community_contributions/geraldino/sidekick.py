from typing import Annotated, List, Any, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sidekick_tools import playwright_tools, other_tools
import uuid
import asyncio
import aiosqlite
import hashlib
from datetime import datetime

load_dotenv(override=True)


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

class State(TypedDict):
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool
    # Clarifier
    clarification_count: int
    clarification_needed: bool
    # Planner
    plan: Optional[List[str]]
    current_task_index: int


# ─────────────────────────────────────────────
# Structured outputs
# ─────────────────────────────────────────────

class ClarifierOutput(BaseModel):
    needs_clarification: bool = Field(description="True if a clarifying question is needed before starting work")
    question: Optional[str] = Field(description="The single clarifying question to ask the user, if needed")


class PlannerOutput(BaseModel):
    plan: List[str] = Field(description="An ordered list of subtasks the worker should complete to fulfill the user's request")


class EvaluatorOutput(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


# ─────────────────────────────────────────────
# User database helpers
# ─────────────────────────────────────────────

USER_DB = "users.db"

async def init_user_db():
    async with aiosqlite.connect(USER_DB) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                sidekick_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def get_user(username: str) -> Optional[Dict]:
    async with aiosqlite.connect(USER_DB) as db:
        async with db.execute(
            "SELECT username, password_hash, sidekick_id FROM users WHERE username = ?", (username,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"username": row[0], "password_hash": row[1], "sidekick_id": row[2]}
    return None


async def create_user(username: str, password: str) -> str:
    sidekick_id = str(uuid.uuid4())
    async with aiosqlite.connect(USER_DB) as db:
        await db.execute(
            "INSERT INTO users (username, password_hash, sidekick_id, created_at) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), sidekick_id, datetime.now().isoformat())
        )
        await db.commit()
    return sidekick_id


async def login_user(username: str, password: str) -> Optional[str]:
    """Returns sidekick_id if login successful, None otherwise."""
    username = username.lower().strip()
    user = await get_user(username)
    if not user:
        # Auto-register new users
        return await create_user(username, password)
    if user["password_hash"] == hash_password(password):
        return user["sidekick_id"]
    return None


# ─────────────────────────────────────────────
# Sidekick
# ─────────────────────────────────────────────

class Sidekick:
    def __init__(self, sidekick_id: str):
        self.sidekick_id = sidekick_id
        self.worker_llm_with_tools = None
        self.clarifier_llm = None
        self.planner_llm = None
        self.evaluator_llm = None
        self.tools = None
        self.graph = None
        self.browser = None
        self.playwright = None
        self._db_conn = None
        self.memory = None

    async def setup(self):
        # SQL-backed memory (persists across restarts)
        self._db_conn = await aiosqlite.connect("sidekick_memory.db")
        self.memory = AsyncSqliteSaver(self._db_conn)

        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)

        self.clarifier_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(ClarifierOutput)
        self.planner_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(PlannerOutput)
        self.evaluator_llm = ChatOpenAI(model="gpt-4o-mini").with_structured_output(EvaluatorOutput)

        await self.build_graph()

    # ── Clarifier ──────────────────────────────

    def clarifier(self, state: State) -> Dict[str, Any]:
        """Ask up to 3 clarifying questions before starting work."""
        count = state.get("clarification_count", 0)

        # If we've already asked 3 questions, skip clarification and proceed
        if count >= 3:
            return {"clarification_needed": False, "clarification_count": count}

        last_human = next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
        )

        system_message = """You are a clarifier agent. Your job is to decide if the user's request 
        is clear enough to act on. If it is ambiguous, missing key details, or could go in very 
        different directions, ask ONE short clarifying question. If the request is clear enough, 
        do not ask anything."""

        user_message = f"""The user said: "{last_human}"

        Success criteria: {state["success_criteria"]}
        Clarifying questions already asked: {count}

        Should we ask a clarifying question, or is this clear enough to proceed?"""

        result = self.clarifier_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        if result.needs_clarification and result.question:
            return {
                "messages": [AIMessage(content=f"Question: {result.question}")],
                "clarification_needed": True,
                "clarification_count": count + 1,
            }
        else:
            return {
                "clarification_needed": False,
                "clarification_count": count,
            }

    def clarifier_router(self, state: State) -> str:
        if state.get("clarification_needed"):
            return "END"  # pause and wait for user to reply
        return "planner"

    # ── Planner ────────────────────────────────

    def planner(self, state: State) -> Dict[str, Any]:
        """Break the request into an ordered list of subtasks."""
        last_human = next(
            (m.content for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), ""
        )

        system_message = """You are a planning agent. Given a user request, break it down into 
        a clear ordered list of subtasks for a worker agent to execute one by one. 
        Keep the plan concise — 2 to 6 steps maximum. Each step should be a single clear action."""

        user_message = f"""User request: "{last_human}"
        Success criteria: {state["success_criteria"]}

        Create an ordered execution plan."""

        result = self.planner_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        return {
            "plan": result.plan,
            "current_task_index": 0,
        }

    # ── Worker ─────────────────────────────────

    def worker(self, state: State) -> Dict[str, Any]:
        plan = state.get("plan") or []
        task_index = state.get("current_task_index", 0)
        current_task = plan[task_index] if plan and task_index < len(plan) else "Complete the user's request"

        plan_display = ""
        if plan:
            plan_display = "\n\nYour execution plan:\n"
            for i, step in enumerate(plan):
                prefix = "✅" if i < task_index else ("👉" if i == task_index else "⬜")
                plan_display += f"  {prefix} Step {i+1}: {step}\n"
            plan_display += f"\nYou are currently on Step {task_index + 1}: {current_task}"

        system_message = f"""You are a helpful assistant that can use tools to complete tasks.
You work through tasks methodically, one step at a time.
You have tools to browse the internet, manage files, run Python code, and search the web.
If you run Python code and need output, always include a print() statement.
The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Success criteria: {state["success_criteria"]}
{plan_display}

When you finish the current step, clearly state you have completed it and what the result was.
If you have a question for the user, prefix it with "Question:" 
If you've completed all steps and the overall task, give the final answer clearly."""

        if state.get("feedback_on_work"):
            system_message += f"""

Previously your reply was rejected. Feedback:
{state["feedback_on_work"]}
Please continue with this feedback in mind."""

        # messages = list(state["messages"])[-5:] # Only use last 5 messages to prevent hallucinations
        all_messages = list(state["messages"])
        messages = all_messages[-10:]
        while messages:
            first = messages[0]
            role = getattr(first, "type", None) or getattr(first, "role", None)
            if role in ("tool", "function"):
                messages = messages[1:]
            elif isinstance(first, AIMessage) and not first.content and not getattr(first, "tool_calls", None):
                messages = messages[1:]
            else:
                break
        found = False
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found = True
        if not found:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    # ── Evaluator ──────────────────────────────

    def format_conversation(self, messages: List[Any]) -> str:
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tool use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> Dict[str, Any]:
        last_response = state["messages"][-1].content
        plan = state.get("plan") or []
        task_index = state.get("current_task_index", 0)

        system_message = """You are an evaluator. Determine if the assistant has successfully 
        completed the current task step and whether the overall success criteria is met."""

        user_message = f"""Conversation:
{self.format_conversation(state["messages"])}

Overall success criteria: {state["success_criteria"]}

Current plan step ({task_index + 1}/{len(plan)}): {plan[task_index] if plan and task_index < len(plan) else "Complete the request"}

Assistant's last response: {last_response}

Has the assistant completed the current step and does the overall work meet the success criteria?
Give feedback. Also flag if user input is needed (question asked, stuck, or needs clarification)."""

        if state.get("feedback_on_work"):
            user_message += f"\n\nPrior feedback given: {state['feedback_on_work']}\nIf the same mistakes repeat, flag user input as needed."

        result = self.evaluator_llm.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message)
        ])

        # Advance to next plan step if current one is done but overall not complete
        new_task_index = task_index
        if result.success_criteria_met is False and not result.user_input_needed:
            if plan and task_index < len(plan) - 1:
                new_task_index = task_index + 1

        return {
            "messages": [{
                "role": "assistant",
                "content": f"Evaluator Feedback: {result.feedback}"
            }],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
            "current_task_index": new_task_index,
        }

    def route_based_on_evaluation(self, state: State) -> str:
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        return "worker"


    # ── Graph ──────────────────────────────────

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        graph_builder.add_edge(START, "clarifier")
        graph_builder.add_conditional_edges(
            "clarifier", self.clarifier_router, {"END": END, "planner": "planner"}
        )
        graph_builder.add_edge("planner", "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    # ── Run ────────────────────────────────────

    async def run_superstep(self, message: str, success_criteria: str, history: list) -> list:
        config = {"configurable": {"thread_id": self.sidekick_id}}
        existing = await self.graph.aget_state(config)
        prev_count = existing.values.get("clarification_count", 0) if existing.values else 0

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "clarification_count": prev_count,
            "clarification_needed": False,
            "plan": None,
            "current_task_index": 0,
        }

        result = await self.graph.ainvoke(state, config=config)

        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    # ── Cleanup ────────────────────────────────

    def cleanup(self):
        async def _cleanup():
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self._db_conn:
                await self._db_conn.close()

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_cleanup())
        except RuntimeError:
            asyncio.run(_cleanup())
