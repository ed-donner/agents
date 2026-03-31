from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from education_coach.nodes import (
    evaluator_node,
    make_evaluator_llm,
    make_worker_llm,
    route_after_evaluation,
    worker_node,
    worker_router,
)
from education_coach.state import State
from education_coach.tools import build_education_tools


def build_app_graph():
    tools = build_education_tools()
    worker_llm = make_worker_llm(tools)
    evaluator_llm = make_evaluator_llm()

    def worker(state: State):
        return worker_node(worker_llm, state)

    def evaluator(state: State):
        return evaluator_node(evaluator_llm, state)

    graph_builder = StateGraph(State)
    graph_builder.add_node("worker", worker)
    graph_builder.add_node("tools", ToolNode(tools=tools))
    graph_builder.add_node("evaluator", evaluator)

    graph_builder.add_conditional_edges(
        "worker",
        worker_router,
        {"tools": "tools", "evaluator": "evaluator"},
    )
    graph_builder.add_edge("tools", "worker")
    graph_builder.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"worker": "worker", "END": END},
    )
    graph_builder.add_edge(START, "worker")

    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory), tools
