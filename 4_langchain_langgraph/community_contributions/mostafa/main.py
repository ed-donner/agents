from dotenv import load_dotenv
load_dotenv(override=True)

from models import *
from kb_state import KBState
from kb_agents import (
    research_planner,
    sme_plan_review,
    search_retrieve,
    sme_source_review,
    content_processor,
    write_outputs
)
from langgraph.graph import StateGraph, END
import os
from typing import Literal


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ─── Routing ───

def plan_review_router(state: KBState) -> Literal["search_retrieval", "research_planner"]:
    """Route based on SME's plan approval."""
    last_message = state["messages"][-1]
    # Parse the SME's decision from the last message
    if 'approved' in last_message['content'].lower().split('_')[0]:
        return "search_retrieval"
    if state.get("plan_revision_count", 0) >= 3:
        return "search_retrieval"  # force proceed after 3 attempts
    return "research_planner"


# ─── Graph Construction ───

def build_graph():
    graph = StateGraph(KBState)

    # Add nodes
    graph.add_node("research_planner", research_planner)
    graph.add_node("sme_plan_review", sme_plan_review)
    graph.add_node("search_retrieval", search_retrieve)
    graph.add_node("sme_source_review", sme_source_review)
    graph.add_node("content_processor", content_processor)
    graph.add_node("write_outputs", write_outputs)

    # Set entry point
    graph.set_entry_point("research_planner")

    # Planning loop
    graph.add_edge("research_planner", "sme_plan_review")
    graph.add_conditional_edges("sme_plan_review", plan_review_router, {
        "search_retrieval": "search_retrieval",
        "research_planner": "research_planner",
    })

    # Linear pipeline after plan approval
    graph.add_edge("search_retrieval", "sme_source_review")
    graph.add_edge("sme_source_review", "content_processor")
    graph.add_edge("content_processor", "write_outputs")
    graph.add_edge("write_outputs", END)

    graph = graph.compile()
    graph.get_graph().draw_mermaid_png(output_file_path="kb_graph.png")
    return graph


if __name__ == "__main__":
    graph = build_graph()
    initial_state: KBState = {
        'topic': 'Network Security Threats and Mitigation Strategies in 2026',
        'kb_name': 'network_security_kb',
        'research_plan': None,
        'plan_feedback': [],
        'plan_revision_count': 0,
        'raw_sources': [],
        'approved_sources': [],
        'rejected_sources': [],
        'kb_entries': [],
        'messages': []
    }
    final_state = graph.invoke(initial_state)
    print("Knowledge base construction complete. Final state:")
    entries = kb_entries = final_state['kb_entries']
    log = final_state['messages']
    with open('communication_log.txt', 'w', encoding='utf-8') as f:
        for message in log:
            f.write(f"{message['role'].upper()}: {message['content']}\n\n")
    with open('kb_entries_summary.txt', 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(f"Title: {entry.title}\n")
            f.write(f"Source URL: {entry.source_url}\n")
            f.write(f"Subtopic: {entry.subtopic}\n")
            f.write(f"Chunk Index: {entry.chunk_index}\n")
            f.write(f"Content Preview: {entry.content[:200]}...\n\n")
    print(final_state)

