import sys
from pathlib import Path

_kica_dir = Path(__file__).resolve().parent
if str(_kica_dir) not in sys.path:
    sys.path.insert(0, str(_kica_dir))

import uuid
import asyncio
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from schema import State, PlannerOutput, EvaluatorOutput
from sidekick_tools import playwright_tools, other_tools, get_researcher_tools, get_executor_tools
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.executor import executor_agent
from agents.evaluator import evaluator_agent

load_dotenv(override=True)


class Sidekick:
    def __init__(self):
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.researcher_tools = None
        self.executor_tools = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        browser_tools, self.browser, self.playwright = await playwright_tools()
        other_tools_list = await other_tools()
        self.researcher_tools = get_researcher_tools(browser_tools, other_tools_list)
        self.executor_tools = get_executor_tools(other_tools_list)

        llm = ChatOpenAI(model="gpt-4o-mini")
        planner_llm = llm.with_structured_output(PlannerOutput)
        researcher_llm = llm.bind_tools(self.researcher_tools)
        executor_llm = llm.bind_tools(self.executor_tools)
        evaluator_llm = llm.with_structured_output(EvaluatorOutput)

        def planner(state: State):
            return planner_agent(planner_llm, state)

        def researcher(state: State):
            return researcher_agent(researcher_llm, state)

        def executor(state: State):
            return executor_agent(executor_llm, state)

        def evaluator(state: State):
            return evaluator_agent(evaluator_llm, state)

        # Routing logic
        def planner_router(state: State) -> str:
            if not state.subtasks:
                return "evaluator"
            return state.subtasks[0].assigned_to

        def researcher_router(state: State) -> str:
            if not state.subtasks:
                return "planner"
            if state.next_subtask_index >= len(state.subtasks):
                return "evaluator"
            next_task = state.subtasks[state.next_subtask_index]
            if next_task.assigned_to != "researcher":
                return next_task.assigned_to
            last = state.messages[-1] if state.messages else None
            if last and hasattr(last, "tool_calls") and last.tool_calls:
                return "researcher_tools"
            return "researcher"

        def executor_router(state: State) -> str:
            if not state.subtasks:
                return "planner"
            if state.next_subtask_index >= len(state.subtasks):
                return "evaluator"
            next_task = state.subtasks[state.next_subtask_index]
            if next_task.assigned_to != "executor":
                return next_task.assigned_to
            last = state.messages[-1] if state.messages else None
            if last and hasattr(last, "tool_calls") and last.tool_calls:
                return "executor_tools"
            return "executor"

        def evaluator_router(state: State) -> str:
            if state.user_input_needed or state.success_criteria_met:
                return "END"
            if state.replan_needed:
                return "planner"
            if state.subtasks and state.next_subtask_index < len(state.subtasks):
                return state.subtasks[state.next_subtask_index].assigned_to
            return "END"

        # Build graph
        builder = StateGraph(State)

        builder.add_node("planner", planner)
        builder.add_node("researcher", researcher)
        builder.add_node("executor", executor)
        builder.add_node("evaluator", evaluator)
        builder.add_node("researcher_tools", ToolNode(self.researcher_tools))
        builder.add_node("executor_tools", ToolNode(self.executor_tools))

        builder.add_edge(START, "planner")
        builder.add_conditional_edges(
            "planner",
            planner_router,
            {"researcher": "researcher", "executor": "executor", "evaluator": "evaluator"},
        )
        builder.add_conditional_edges(
            "researcher",
            researcher_router,
            {
                "researcher": "researcher",
                "researcher_tools": "researcher_tools",
                "executor": "executor",
                "evaluator": "evaluator",
                "planner": "planner",
            },
        )
        builder.add_conditional_edges(
            "executor",
            executor_router,
            {
                "executor": "executor",
                "executor_tools": "executor_tools",
                "researcher": "researcher",
                "evaluator": "evaluator",
                "planner": "planner",
            },
        )
        builder.add_conditional_edges(
            "evaluator",
            evaluator_router,
            {
                "planner": "planner",
                "researcher": "researcher",
                "executor": "executor",
                "END": END,
            },
        )
        builder.add_edge("researcher_tools", "researcher")
        builder.add_edge("executor_tools", "executor")

        self.graph = builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        state: dict[str, Any] = {
            "messages": [HumanMessage(content=message)] if isinstance(message, str) else message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
            "plan": None,
            "subtasks": None,
            "next_subtask_index": 0,
            "subtask_results": [],
            "replan_needed": False,
            "final_answer": None,
        }

        result = await self.graph.ainvoke(
            state,
            config={**config, "recursion_limit": 50},
        )

        # Extract last AI response for display
        last_ai = None
        for m in reversed(result.get("messages", [])):
            if isinstance(m, AIMessage) and m.content:
                last_ai = m.content
                break

        if last_ai is None:
            last_ai = (
                (result.get("subtask_results") or [""])[-1]
                or "No response generated."
            )

        user = {"role": "user", "content": message if isinstance(message, str) else str(message)}
        reply = {"role": "assistant", "content": last_ai}
        return history + [user, reply]

    def cleanup(self):
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
