"""Graph assembly — nodes, edges, routing, and checkpointer"""

import os
import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from agent.state import State
from agent.tools import tools
from agent.nodes import intake, search, format_results, route_entry, route_intake, search_router


def build_graph(db_path: str = None):
    """Construct and compile the Kigali Property Scout graph."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "kigali_scout.db")

    builder = StateGraph(State)

    builder.add_node("intake", intake)
    builder.add_node("search", search)
    builder.add_node("tools", ToolNode(tools=tools))
    builder.add_node("format", format_results)

    builder.add_conditional_edges(START, route_entry, {"intake": "intake", "search": "search"})
    builder.add_conditional_edges("intake", route_intake, {"search": "search", "end": END})
    builder.add_conditional_edges("search", search_router, {"tools": "tools", "format": "format"})
    builder.add_edge("tools", "search")
    builder.add_edge("format", END)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    memory = SqliteSaver(conn)

    return builder.compile(checkpointer=memory)
