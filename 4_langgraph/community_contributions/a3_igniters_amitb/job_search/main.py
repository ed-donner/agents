from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import uuid
import asyncio

from tools import add_tools
from state import State
from job_search import config


class JobsSearchAssistant:
    def __init__(self):
        self.tools = None
        self.graph = None
        self.thread_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def setup(self):
        self.tools = await add_tools()
        await self.build_graph()

    def route_after_primary(self, state: State) -> str:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return config.INPUT_GUARDRAILS_ASSISTANT

    def route_after_tools(self, state: State) -> str:
        """Return to whichever node issued the last tool_calls; ToolNode only appends tool messages."""
        last = state.get("last_assistant")
        if last == config.EXECUTOR_ASSISTANT:
            return config.EXECUTOR_ASSISTANT
        return config.PRIMARY_ASSISTANT

    def route_after_input_guardrails(self, state: State) -> str:
        """
        PASS (safe / valid): success_criteria_met -> planner.
        NEED USER: user_input_needed -> END (pause; next user turn continues same thread).
        FAIL: retry primary with feedback already written by the guardrails node.
        """
        if state.get("user_input_needed"):
            return "END"
        if state.get("success_criteria_met"):
            return config.PLANNER_ASSISTANT
        return config.PRIMARY_ASSISTANT

    def route_after_executor(self, state: State) -> str:
        last = state["messages"][-1]
        if getattr(last, "tool_calls", None):
            return "tools"
        return config.OUTPUT_GUARDRAILS_ASSISTANT

    def route_after_output_guardrails(self, state: State) -> str:
        if state.get("user_input_needed"):
            return "END"
        if state.get("success_criteria_met"):
            return config.OUTPUT_MANAGER_ASSISTANT
        return config.PRIMARY_ASSISTANT

    async def build_graph(self):
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node(config.PRIMARY_ASSISTANT, self.primary_assistant)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node(config.INPUT_GUARDRAILS_ASSISTANT, self.input_guardrails_assistant)
        graph_builder.add_node(config.PLANNER_ASSISTANT, self.planner_assistant)
        graph_builder.add_node(config.EXECUTOR_ASSISTANT, self.executor_assistant)
        graph_builder.add_node(config.OUTPUT_GUARDRAILS_ASSISTANT, self.output_guardrails_assistant)
        graph_builder.add_node(config.OUTPUT_MANAGER_ASSISTANT, self.output_manager_assistant)

        # Add edges
        # START -> Primary (router in diagram)
        graph_builder.add_edge(START, config.PRIMARY_ASSISTANT)

        # Primary: tools loop OR continue to input guardrails
        graph_builder.add_conditional_edges(
            config.PRIMARY_ASSISTANT,
            self.route_after_primary,
            {
                "tools": "tools",
                config.INPUT_GUARDRAILS_ASSISTANT: config.INPUT_GUARDRAILS_ASSISTANT,
            },
        )

        # Shared ToolNode: return to whoever called tools
        graph_builder.add_conditional_edges(
            "tools",
            self.route_after_tools,
            {
                "primary_assistant": config.PRIMARY_ASSISTANT,
                "executor_assistant": config.EXECUTOR_ASSISTANT,
            },
        )

        # Guardrails: PASS -> planner; FAIL -> primary; need user -> END
        graph_builder.add_conditional_edges(
            config.INPUT_GUARDRAILS_ASSISTANT,
            self.route_after_input_guardrails,
            {
                "planner_assistant": config.PLANNER_ASSISTANT,
                "primary_assistant": config.PRIMARY_ASSISTANT,
                "END": END,
            },
        )

        # Planner -> Executor (single happy path; add a router here if planner can reject)
        graph_builder.add_edge(config.PLANNER_ASSISTANT, config.EXECUTOR_ASSISTANT)

        # Executor: tools loop OR hand off to output pipeline
        graph_builder.add_conditional_edges(
            config.EXECUTOR_ASSISTANT,
            self.route_after_executor,
            {
                "tools": "tools",
                "output_guardrails_assistant": config.OUTPUT_GUARDRAILS_ASSISTANT,
            },
        )

        # Output chain
        graph_builder.add_conditional_edges(
            config.OUTPUT_GUARDRAILS_ASSISTANT,
            self.route_after_output_guardrails,
            {
                "output_manager_assistant": config.OUTPUT_MANAGER_ASSISTANT,
                "executor_assistant": config.EXECUTOR_ASSISTANT,
                "END": END,
            },
        )
        graph_builder.add_edge(config.OUTPUT_MANAGER_ASSISTANT, END)

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        graph_config = {"configurable": {"thread_id": self.thread_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "feedback": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=graph_config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
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
