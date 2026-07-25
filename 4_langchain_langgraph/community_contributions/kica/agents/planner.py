from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from schema import PlannerOutput, State


def planner_agent(llm_with_output: Runnable, state: State) -> dict[str, Any]:
    replan_context = ""
    if getattr(state, "replan_needed", False) and getattr(state, "feedback_on_work", None):
        replan_context = f"""

    Previously you thought you had a good plan, but the execution failed.
    Here is the feedback on why it was rejected:
    {state.feedback_on_work}
    With this feedback, please produce a NEW plan that addresses the failure. Do not repeat the same approach."""

    system_message = f"""You are the PLANNER. Convert the user's request into an executable plan.
    Assign each subtask to exactly one agent: researcher (search, browse, Wikipedia) or executor (files, Python, push notifications).
    Subtasks must be ordered by dependency. Each subtask must be self-contained.
    Do NOT write "Use the search results" - include what to find in the task text.
    For multiple independent lookups, combine into one subtask (e.g. "Search for X, Y, and Z").
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    {replan_context}
    """

    messages = list(state.messages) if state.messages else []
    human_content = "No conversation yet."
    for m in reversed(messages):
        if isinstance(m, HumanMessage) and m.content:
            human_content = f"User request:\n{m.content}\n\nGenerate the plan, subtasks, and success criteria."
            break

    response: PlannerOutput = llm_with_output.invoke(
        [SystemMessage(content=system_message), HumanMessage(content=human_content)]
    )

    from langchain_core.messages import AIMessage

    return {
        "plan": response.plan,
        "subtasks": response.subtasks,
        "success_criteria": response.success_criteria,
        "next_subtask_index": 0,
        "subtask_results": [],
        "replan_needed": False,
        "messages": [
            AIMessage(content=f"Plan: {response.plan}\n\nSubtasks: {[s.task for s in response.subtasks]}"),
        ],
    }
