from schema import State, ClarifierOutput, PlannerOutput, EvaluatorOutput, FinalizerOutput
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from agents.clarifier import clarifier_agent, format_conversation
from agents.planner import planner_agent
from agents.finalizer import finalizer_agent
from db.sql_memory import setup_memory, init_preferences_table, load_preferences, save_preferences
from sidekick_tools import playwright_tools, other_tools
from datetime import datetime
from typing import Dict, Any
import uuid
import asyncio


class Sidekick:
    def __init__(self):
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.clarifier_llm_with_output = None
        self.planner_llm_with_output = None
        self.finalizer_llm_with_output = None
        self.tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None
        self.browser = None
        self.playwright = None
        self.user_preferences = {}

    async def setup(self):
        await init_preferences_table()
        self.memory = await setup_memory()
        self.user_preferences = await load_preferences()

        self.tools, self.browser, self.playwright = await playwright_tools()
        self.tools += await other_tools()

        self.clarifier_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            ClarifierOutput, method="function_calling"
        )
        self.planner_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            PlannerOutput, method="function_calling"
        )
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        self.evaluator_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            EvaluatorOutput, method="function_calling"
        )
        self.finalizer_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(
            FinalizerOutput, method="function_calling"
        )

        await self.build_graph()

    def clarifier(self, state: State) -> dict:
        result = clarifier_agent(self.clarifier_llm_with_output, state, self.user_preferences)
        result.setdefault("intent_type", "conversational")
        return result

    def clarifier_router(self, state: State) -> str:
        if state.intent_type == "conversational":
            return "finalizer"
        if state.user_input_needed and state.clarification_round < state.max_clarifications:
            return "END"
        if state.intent_type == "actionable":
            return "planner"
        return "END"

    def planner(self, state: State) -> dict:
        return planner_agent(self.planner_llm_with_output, state, self.user_preferences)

    def worker(self, state: State) -> Dict[str, Any]:
        current_task = ""
        if state.subtasks and state.next_subtask_index < len(state.subtasks):
            current_task = state.subtasks[state.next_subtask_index].task

        system_message = f"""You are a helpful assistant that uses tools to complete tasks.

Current task: {current_task}
Success criteria: {state.success_criteria}
Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

You have tools for browsing the web, searching, running Python code, and managing files.
If you need to run Python code, include print() statements to see output.
Complete the current task, then provide your result.
"""

        if state.feedback_on_work:
            system_message += f"""
Your previous attempt was rejected. Feedback: {state.feedback_on_work}
Address this feedback in your next attempt.
"""

        found_system = False
        messages = list(state.messages)
        for msg in messages:
            if isinstance(msg, SystemMessage):
                msg.content = system_message
                found_system = True
        if not found_system:
            messages = [SystemMessage(content=system_message)] + messages

        response = self.worker_llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def worker_router(self, state: State) -> str:
        last_message = state.messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "evaluator"

    def evaluator(self, state: State) -> dict:
        last_response = state.messages[-1].content

        system_message = f"""You are an evaluator that determines if a task has been completed successfully.
Assess the assistant's last response. Respond with feedback, whether success criteria are met, and whether user input is needed."""

        user_message = f"""Conversation:
{format_conversation(state.messages)}

Success criteria: {state.success_criteria}

Last response to evaluate: {last_response}

Decide if the criteria are met, or if more user input is required."""

        if state.feedback_on_work:
            user_message += f"\nPrevious feedback: {state.feedback_on_work}\nIf the assistant repeats mistakes, request user input."

        result: EvaluatorOutput = self.evaluator_llm_with_output.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ])

        new_retry_count = state.retry_count + (0 if result.success_criteria_met else 1)

        updates = {
            "messages": [AIMessage(content=f"Evaluator: {result.feedback}")],
            "feedback_on_work": result.feedback,
            "success_criteria_met": result.success_criteria_met,
            "user_input_needed": result.user_input_needed,
            "retry_count": new_retry_count,
        }

        if result.success_criteria_met and state.subtasks:
            updates["next_subtask_index"] = state.next_subtask_index + 1

        return updates

    def evaluator_router(self, state: State) -> str:
        if state.user_input_needed:
            return "clarifier"
        if state.success_criteria_met:
            if state.subtasks and state.next_subtask_index < len(state.subtasks):
                return "worker"
            return "finalizer"
        if state.retry_count >= 2:
            return "finalizer"
        return "worker"

    def finalizer(self, state: State) -> dict:
        updates, extracted_prefs = finalizer_agent(self.finalizer_llm_with_output, state)
        if extracted_prefs:
            self._pending_preferences = extracted_prefs
        return updates

    async def build_graph(self):
        graph_builder = StateGraph(State)

        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_node("finalizer", self.finalizer)

        graph_builder.add_edge(START, "clarifier")
        graph_builder.add_conditional_edges(
            "clarifier", self.clarifier_router, {"END": END, "planner": "planner", "finalizer": "finalizer"}
        )
        graph_builder.add_edge("planner", "worker")
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.evaluator_router,
            {"clarifier": "clarifier", "worker": "worker", "finalizer": "finalizer"}
        )
        graph_builder.add_edge("finalizer", END)

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, history):
        config = {"configurable": {"thread_id": self.sidekick_id}, "recursion_limit": 100}
        self._pending_preferences = None

        state = {
            "messages": [HumanMessage(content=message)],
        }
        result = await self.graph.ainvoke(state, config=config)

        if self._pending_preferences:
            await save_preferences(self._pending_preferences)
            self.user_preferences.update(self._pending_preferences)

        last_ai = next(
            (m for m in reversed(result["messages"]) if isinstance(m, AIMessage)),
            None,
        )

        if last_ai:
            history = history + [
                {"role": "assistant", "content": last_ai.content},
            ]

        needs_input = result.get("user_input_needed", False)
        return history, needs_input

    async def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
        if self.memory and hasattr(self.memory, "conn"):
            await self.memory.conn.close()
