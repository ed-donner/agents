from langgraph.graph import StateGraph, END
from state import CareerState

from nodes.manager import manager_node
from nodes.clarifier import clarifier_node
from nodes.researcher import research_node
from nodes.skill_gap import skill_gap_node
from nodes.learning_plan import learning_plan_node
from nodes.final_report import final_report_node

def route_manager(state):
    return state["next_step"]
def build_graph():
    builder = StateGraph(CareerState)

    builder.add_node("manager", manager_node)
    builder.add_node("clarifier", clarifier_node)
    builder.add_node("research", research_node)
    builder.add_node("skill_gap", skill_gap_node)
    builder.add_node("learning_plan", learning_plan_node)
    builder.add_node("final", final_report_node)

    builder.set_entry_point("manager")

    builder.add_conditional_edges(
        "manager",
        route_manager,
        {
            "clarifier": "clarifier",
            "research": "research"
        }
    )

    builder.add_edge("clarifier", "manager")
    builder.add_edge("research", "skill_gap")
    builder.add_edge("skill_gap", "learning_plan")
    builder.add_edge("learning_plan", "final")
    builder.add_edge("final", END)

    return builder.compile()