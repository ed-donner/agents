from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from backend.web_search import search_code_examples
from backend.llm_client import generate_plan
from backend.file_creator import create_project
from backend.utils.logger import get_logger

logger = get_logger()


class State(TypedDict):
    session_id: str
    state: Literal["challenge", "plan", "build"]
    challenge: str
    language: str
    plan: str
    build_status: str


def challenge_node(state: State) -> State:
    logger.log_workflow_node(
        node_name="challenge_node",
        session_id=state.get("session_id", "unknown"),
        state={
            "current_state": state.get("state"),
            "challenge": state.get("challenge", "")[:50],
        },
    )
    new_state = dict(state)
    new_state["language"] = "python"
    new_state["state"] = "plan"
    logger.log_state_transition(
        session_id=state.get("session_id", "unknown"),
        from_state=state.get("state", "unknown"),
        to_state="plan",
        context={"node": "challenge_node", "language": "python"},
    )
    return new_state


def plan_node(state: State) -> State:
    session_id = state.get("session_id", "unknown")
    logger.log_workflow_node(
        node_name="plan_node",
        session_id=session_id,
        state={
            "current_state": state.get("state"),
            "challenge": state.get("challenge", "")[:50],
            "language": state.get("language", ""),
        },
    )

    try:
        search_results = search_code_examples(state["challenge"], state["language"])
        plan = generate_plan(state["challenge"], state["language"], search_results)
        new_state = dict(state)
        new_state["plan"] = plan
        new_state["state"] = "build"

        logger.log_state_transition(
            session_id=session_id,
            from_state=state.get("state", "unknown"),
            to_state="build",
            context={
                "node": "plan_node",
                "plan_length": len(plan),
                "search_results_count": len(search_results) if search_results else 0,
            },
        )
        return new_state
    except Exception as e:
        logger.log_workflow_node(
            node_name="plan_node", session_id=session_id, state=state, error=str(e)
        )
        raise


def build_node(state: State) -> State:
    session_id = state.get("session_id", "unknown")
    logger.log_workflow_node(
        node_name="build_node",
        session_id=session_id,
        state={
            "current_state": state.get("state"),
            "language": state.get("language", ""),
            "plan_length": len(state.get("plan", "")),
        },
    )

    try:
        result = create_project(state["plan"], state["language"], state["session_id"])
        new_state = dict(state)
        new_state["build_status"] = result["status"]
        new_state["state"] = "build"

        logger.log_state_transition(
            session_id=session_id,
            from_state=state.get("state", "unknown"),
            to_state="build",
            context={
                "node": "build_node",
                "status": result["status"],
                "files_created": len(result.get("files_created", [])),
            },
        )
        return new_state
    except Exception as e:
        logger.log_workflow_node(
            node_name="build_node", session_id=session_id, state=state, error=str(e)
        )
        raise


def router_node(state: State) -> State:
    return state


def route_next_step(state: State) -> str:
    current_state = state.get("state", "challenge")
    if current_state == "challenge":
        return "challenge_step"
    elif current_state == "plan":
        return "build_step"
    else:
        return END


def execute_plan_workflow(state: State) -> State:
    session_id = state.get("session_id", "unknown")
    logger.logger.info(f"Starting plan workflow execution for session {session_id}")
    try:
        state["language"] = "python"
        config = {"configurable": {"thread_id": session_id}}
        result = app.invoke(state, config=config)
        logger.logger.info(
            f"Plan workflow completed successfully for session {session_id}"
        )
        return result
    except Exception as e:
        logger.logger.error(
            f"Plan workflow failed for session {session_id}: {str(e)}", exc_info=True
        )
        raise


def execute_build_workflow(state: State) -> State:
    session_id = state.get("session_id", "unknown")
    logger.logger.info(f"Starting build workflow execution for session {session_id}")
    try:
        config = {"configurable": {"thread_id": session_id}}
        result = app.invoke(state, config=config)
        logger.logger.info(
            f"Build workflow completed successfully for session {session_id}"
        )
        return result
    except Exception as e:
        logger.logger.error(
            f"Build workflow failed for session {session_id}: {str(e)}", exc_info=True
        )
        raise


workflow = StateGraph(State)

workflow.add_node("router", router_node)
workflow.add_node("challenge_step", challenge_node)
workflow.add_node("plan_step", plan_node)
workflow.add_node("build_step", build_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    route_next_step,
    {
        "challenge_step": "challenge_step",
        "build_step": "build_step",
        END: END,
    },
)

workflow.add_edge("challenge_step", "plan_step")

workflow.add_conditional_edges(
    "plan_step",
    route_next_step,
    {
        "build_step": "build_step",
        END: END,
    },
)

workflow.add_edge("build_step", END)

app = workflow.compile()
