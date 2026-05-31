from schema import ExecutorToolInference, PlannerOutput, State, EvaluatorOutput, ClarifierOutput, FinalizerOutput, ResearcherToolInference
from langgraph.graph import StateGraph, START, END
from langgraph.types import Interrupt
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from tools.file_code import file_code_tools
from tools.navigation import playwright_tools
from tools.search import search_tools
from tools.notifications import whatsapp_tool
from agents.clarifier import clarifier_agent
from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.summarizer import summarizer_agent
from agents.executor import executor_agent
from agents.evaluator import evaluator_agent
from agents.finalizer import finalizer_agent
from db.sql_memory import setup_memory
from utils.utils import infer_tool_calls
import uuid
import asyncio


class Sidekick:
    def __init__(self):
        self.clarifier_llm_with_output = None
        self.planner_llm_with_output = None
        self.researcher_llm_with_tools = None
        self.summarizer_llm = None
        self.executor_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.finalizer_llm_with_output = None
        self.researcher_tools = None
        self.executor_tools = None
        self.graph = None
        self.sidekick_id = str(uuid.uuid4())
        self.memory = None
        self.browser = None
        self.playwright = None

    async def setup(self):
        self.memory = await setup_memory()
        self.researcher_tools, self.browser, self.playwright = await playwright_tools()
        self.researcher_tools += await search_tools()
        self.executor_tools = await file_code_tools()
        self.executor_tools.append(whatsapp_tool)
        self.clarifier_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(ClarifierOutput, method="function_calling")
        self.planner_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(PlannerOutput, method="function_calling")
        self.researcher_llm_with_tools = ChatOpenAI(model="gpt-4o-mini").bind_tools(self.researcher_tools)
        self.executor_llm_with_tools = ChatOpenAI(model="gpt-4o-mini").bind_tools(self.executor_tools)
        self.summarizer_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(EvaluatorOutput)
        self.finalizer_llm_with_output = ChatOpenAI(model="gpt-4o-mini").with_structured_output(FinalizerOutput)
        await self.build_graph()

    def clarifier(self, state: State) -> State:
        return clarifier_agent(self.clarifier_llm_with_output, state)

    def wait_for_user(self, state: State):
        return Interrupt("waiting_for_user")

    def planner(self, state: State) -> State:
        return planner_agent(self.planner_llm_with_output, state)

    def researcher(self, state: State) -> State:
        return researcher_agent(self.researcher_llm_with_tools, state)

    def summarizer(self, state: State) -> State:
        return summarizer_agent(self.summarizer_llm, state)

    def executor(self, state: State) -> State:
        return executor_agent(self.executor_llm_with_tools, state)

    def evaluator(self, state: State) -> State:
        return evaluator_agent(self.evaluator_llm_with_output, state)

    def finalizer(self, state: State) -> State:
        return finalizer_agent(self.finalizer_llm_with_output, state)

    def clarifier_router(self, state: State) -> str:
        if state.user_input_needed:
            return "wait"
        if state.side_effects_requested and state.user_side_effects_confirmed is not None:
            return "evaluator"
        return "planner"

    def planner_router(self, state: State) -> str:
        if not state.subtasks:
            return "evaluator"
        next_task = state.subtasks[0]
        return next_task.assigned_to

    def researcher_router(self, state: State) -> str:

        # 1. No plan yet
        if not state.subtasks:
            return "planner"

        # 2. All tasks done
        if state.next_subtask_index >= len(state.subtasks):
            return "evaluator"

        next_task = state.subtasks[state.next_subtask_index]

        # 3. Task not for researcher → hand off
        if next_task.assigned_to != "researcher":
            return next_task.assigned_to

        # 4. Tool call in progress
        if state.messages:
            last = state.messages[-1]
            tools = infer_tool_calls(last)
            if tools:
                if all(isinstance(t, ResearcherToolInference) for t in tools):
                    return "researcher_tools"
                else:
                    return "researcher"

        # 5. Otherwise keep researching
        return "researcher"

    def summarizer_router(self, state: State) -> str:
        # 1. No plan yet
        if not state.subtasks:
            return "planner"

        # 2. All tasks done
        if state.next_subtask_index >= len(state.subtasks):
            return "evaluator"

        next_task = state.subtasks[state.next_subtask_index]

        # 3. Task not for researcher → hand off
        if next_task.assigned_to != "summarizer":
            return next_task.assigned_to

        return "summarizer"

    def executor_router(self, state: State) -> str:

        # 1. No plan yet
        if not state.subtasks:
            return "planner"

        # 2. All tasks done
        if state.next_subtask_index >= len(state.subtasks):
            return "evaluator"

        next_task = state.subtasks[state.next_subtask_index]

        # 3. Task not for researcher → hand off
        if next_task.assigned_to != "executor":
            return next_task.assigned_to

        if state.side_effects_requested and not state.side_effects_approved:
            return "evaluator"

        if state.messages:
            last = state.messages[-1]
            tools = infer_tool_calls(last)
            if tools:
                if all(isinstance(t, ExecutorToolInference) for t in tools):
                    return "executor_tools"
                else:
                    return "executor"

        return "executor"

    def evaluator_router(self, state: State) -> str:
        if state.user_input_needed:
            return "clarifier"

        if state.next_subtask_index < len(state.subtasks):
            return state.subtasks[state.next_subtask_index].assigned_to

        if not state.success_criteria_met:
            if state.replan_needed:
                return "planner"
            else:
                return "finalizer"

        return "finalizer"

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("clarifier", self.clarifier)
        graph_builder.add_node("wait_for_user", self.wait_for_user)
        graph_builder.add_node("planner", self.planner)
        graph_builder.add_node("researcher", self.researcher)
        graph_builder.add_node("summarizer", self.summarizer)
        graph_builder.add_node("executor", self.executor)
        graph_builder.add_node("evaluator", self.evaluator)
        graph_builder.add_node("finalizer", self.finalizer)
        graph_builder.add_node("researcher_tools", ToolNode(tools=self.researcher_tools))
        graph_builder.add_node("executor_tools", ToolNode(tools=self.executor_tools))

        # Add edges
        graph_builder.add_edge(START, "clarifier")
        graph_builder.add_conditional_edges(
            "clarifier",
            self.clarifier_router,
            {
                "wait": "wait_for_user",
                "planner": "planner",
                "evaluator": "evaluator",
                "finalizer": "finalizer"
            }
        )
        graph_builder.add_conditional_edges(
            "planner",
            self.planner_router,
            {
                "researcher": "researcher",
                "executor": "executor",
                "summarizer": "summarizer",
                "evaluator": "evaluator"
            }
        )
        graph_builder.add_conditional_edges(
            "researcher",
            self.researcher_router,
            {
                "researcher_tools": "researcher_tools",
                "planner": "planner",
                "researcher": "researcher",
                "executor": "executor",
                "summarizer": "summarizer",
                "evaluator": "evaluator"
            }
        )
        graph_builder.add_conditional_edges(
            "summarizer",
            self.summarizer_router,
            {
                "clarifier": "clarifier",
                "planner": "planner",
                "researcher": "researcher",
                "executor": "executor",
                "summarizer": "summarizer",
                "evaluator": "evaluator"
            }
        )
        graph_builder.add_conditional_edges(
            "executor",
            self.executor_router,
            {
                "executor_tools": "executor_tools",
                "planner": "planner",
                "researcher": "researcher",
                "executor": "executor",
                "summarizer": "summarizer",
                "evaluator": "evaluator"
            }
        )
        graph_builder.add_conditional_edges(
            "evaluator",
            self.evaluator_router,
            {
                "clarifier": "clarifier",
                "planner": "planner",
                "researcher": "researcher",
                "executor": "executor",
                "summarizer": "summarizer",
                "evaluator": "evaluator",
                "finalizer": "finalizer"
            }
        )
        graph_builder.add_edge("researcher_tools", "researcher")
        graph_builder.add_edge("executor_tools", "executor")
        graph_builder.add_edge("finalizer", END)

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, history):
        config = {"configurable": {"thread_id": self.sidekick_id}}

        if isinstance(message, str):
            message = HumanMessage(content=message)

        # Invoke graph with ONLY the new message
        result = await self.graph.ainvoke(
            {"messages": [message]},
            config=config,
        )

        last_ai = next(
            (m for m in reversed(result["messages"]) if isinstance(m, AIMessage)),
            None,
        )

        if last_ai:
            history = history + [
                {"role": "user", "content": message.content},
                {"role": "assistant", "content": last_ai.content},
            ]

        # True if graph paused for user input or permission
        user_input_needed = "__interrupt__" in result

        return history, user_input_needed

    async def cleanup(self):
        if self.browser:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.browser.close())
                if self.playwright:
                    loop.create_task(self.playwright.stop())
            except RuntimeError:
                # If no loop is running, do a direct run
                asyncio.run(self.browser.close())
                if self.playwright:
                    asyncio.run(self.playwright.stop())
        if self.memory and hasattr(self.memory, "conn"):
            await self.memory.conn.close()
