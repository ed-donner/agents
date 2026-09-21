"""
SideKick LangGraph agent graph.

Flow:
  START → router → tool_fetcher → [email|calendar|tasks|research|general] → END
"""

from langgraph.graph import StateGraph, START, END
from agents.state import AgentState
from agents.router import router_node
from agents.tool_fetcher import tool_fetcher_node
from agents.email_agent import email_node
from agents.calendar_agent import calendar_node
from agents.tasks_agent import tasks_node
from agents.research_agent import research_node
from agents.general_agent import general_node


def _route_by_intent(state: AgentState) -> str:
    """Conditional edge: route to the correct specialist node."""
    return state.intent  # returns one of: email, calendar, tasks, research, general


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("tool_fetcher", tool_fetcher_node)
    graph.add_node("email", email_node)
    graph.add_node("calendar", calendar_node)
    graph.add_node("tasks", tasks_node)
    graph.add_node("research", research_node)
    graph.add_node("general", general_node)

    # Edges
    graph.add_edge(START, "router")
    graph.add_edge("router", "tool_fetcher")

    graph.add_conditional_edges(
        "tool_fetcher",
        _route_by_intent,
        {
            "email": "email",
            "calendar": "calendar",
            "tasks": "tasks",
            "research": "research",
            "general": "general",
        },
    )

    graph.add_edge("email", END)
    graph.add_edge("calendar", END)
    graph.add_edge("tasks", END)
    graph.add_edge("research", END)
    graph.add_edge("general", END)

    return graph.compile()


# Module-level compiled graph instance
sidekick_graph = build_graph()
