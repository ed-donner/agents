"""
Agentic Graph
"""

import uuid
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .nodes import Nodes
from .tools import Tools
from .state.state import State
from .state.evaluator_output import EvaluatorOutput


class Graph:
    def __init__(self):
        self.thread_id = str(uuid.uuid4())
        self.memory = MemorySaver()
        self.nodes = Nodes()
        self.tools = Tools()
        self.graph = None
        self._tools_list = None

    async def setup(self):
        """Initialize nodes (LLMs, tools) and build the graph."""
        self._tools_list = [
            self.tools._serper_tool(),
            self.tools._wikipedia_tool(),
            self.tools._python_repl_tool(),
        ]
        llm = ChatOpenAI(model=self.nodes.model)
        self.nodes.llm_with_tools = llm.bind_tools(self._tools_list)
        evaluator_llm = ChatOpenAI(model=self.nodes.model)
        self.nodes.evaluator_llm_with_output = evaluator_llm.with_structured_output(
            EvaluatorOutput
        )
        self._build_graph()

    def get_graph(self):
        """
        Grabs an instance of the agentic graph.
        """
        if self.graph is None:
            self._build_graph()

        return self.graph

    def _build_graph(self):
        """
        Building agentic graph.
        """
        if self._tools_list is None:
            self._tools_list = [
                self.tools._serper_tool(),
                self.tools._wikipedia_tool(),
                self.tools._python_repl_tool(),
            ]
        graph_builder = StateGraph(State)

        graph_builder.add_node("worker", self.nodes.worker_node)
        graph_builder.add_node("tools", ToolNode(tools=self._tools_list))
        graph_builder.add_node("evaluator", self.nodes.evaluator_node)

        graph_builder.add_edge(START, "worker")
        graph_builder.add_conditional_edges(
            "worker",
            self._worker_router,
            {"tools": "tools", "evaluator": "evaluator"},
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator",
            self._route_based_on_evaluation,
            {"worker": "worker", "END": END},
        )

        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        """Run one conversation turn: user message -> agent response -> evaluator feedback."""
        config = {
            "configurable": {"thread_id": self.thread_id},
            "recursion_limit": 50,
        }

        state = {
            "messages": [HumanMessage(content=message)],
            "success_criteria": success_criteria or "The answer should be clear and accurate",
            "success_criteria_met": False,
            "feedback_on_work": None,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        messages = result.get("messages", [])

        user = {"role": "user", "content": message}
        reply_content = messages[-2].content if len(messages) >= 2 else ""
        feedback_content = messages[-1].content if len(messages) >= 1 else ""
        reply = {"role": "assistant", "content": reply_content}
        feedback = {"role": "assistant", "content": feedback_content}
        return (history or []) + [user, reply, feedback]

    def cleanup(self):
        """Release resources. No browser/playwright in this implementation."""
        pass
    
    @staticmethod
    def _worker_router(state: State) -> Literal["tools", "evaluator"]:
        """
        Routes based on the worker's nodes output.
        """
        last_message = state.messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"
    
    @staticmethod
    def _route_based_on_evaluation(state: State) -> Literal["worker", "END"]:
        """
        Routes based on the evaluation of the worker's nodes output.
        """
        if state.success_criteria_met or state.user_input_needed:
            return "END"
        else:
            return "worker"