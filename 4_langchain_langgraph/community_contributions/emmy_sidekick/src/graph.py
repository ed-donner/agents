"""Graph construction and routing logic"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.models import State
from src.nodes import (
    planner,
    research,
    generate_guide,
    ask_refinement,
    handle_refinement,
    youtube_search_node
)


def route_start(state: State) -> str:
    """
    Route from START based on current stage
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    stage = state.get("stage", "gather_info")
    
    # If completed, don't process any more messages
    if stage == "completed":
        return "end"
    elif stage == "await_refinement":
        return "handle_refinement"
    else:
        return "planner"


def route_planner(state: State) -> str:
    """
    Decide where to go from planner
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    stage = state.get("stage", "gather_info")
    
    if stage == "research":
        return "research"
    else:
        return "end"


def route_refinement(state: State) -> str:
    """
    Decide what to do after handling refinement
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    stage = state.get("stage", "await_refinement")
    
    if stage == "completed":
        return "completed"
    elif stage == "ask_refinement":
        return "ask"
    elif stage == "youtube_search":
        return "youtube"
    else:
        return "handle"


def build_graph():
    """
    Construct the interview prep agent graph
    
    Returns:
        Compiled LangGraph graph with memory checkpointing
    """
    # Initialize graph builder
    builder = StateGraph(State)
    
    # Add all nodes
    builder.add_node("planner", planner)
    builder.add_node("research", research)
    builder.add_node("generate", generate_guide)
    builder.add_node("ask_refinement", ask_refinement)
    builder.add_node("handle_refinement", handle_refinement)
    builder.add_node("youtube_search", youtube_search_node)
    
    # Entry point routing
    builder.add_conditional_edges(
        START,
        route_start,
        {
            "planner": "planner",
            "handle_refinement": "handle_refinement",
            "end": END
        }
    )
    
    # Planner routing
    builder.add_conditional_edges(
        "planner",
        route_planner,
        {
            "end": END,
            "research": "research"
        }
    )
    
    # Research → Generate → Ask for refinement
    builder.add_edge("research", "generate")
    builder.add_edge("generate", "ask_refinement")
    
    # Refinement loop
    builder.add_edge("ask_refinement", END)
    
    builder.add_conditional_edges(
        "handle_refinement",
        route_refinement,
        {
            "ask": "ask_refinement",
            "completed": END,
            "youtube": "youtube_search",
            "handle": "handle_refinement"
        }
    )
    
    # YouTube search returns to refinement state
    builder.add_edge("youtube_search", END)
    
    # Compile with memory checkpointing
    memory = MemorySaver()
    graph = builder.compile(checkpointer=memory)
    
    return graph

