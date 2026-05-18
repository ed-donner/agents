from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable

from schema import EvaluatorOutput, State


def format_conversation(messages) -> str:
    conversation = "Conversation history:\n\n"
    for m in messages or []:
        if isinstance(m, HumanMessage):
            conversation += f"User: {m.content}\n"
        elif isinstance(m, AIMessage):
            text = m.content or "[Tools use]"
            conversation += f"Assistant: {text}\n"
    return conversation or "(none)"


def evaluator_agent(llm_with_output: Runnable, state: State) -> dict[str, Any]:
    subtasks = state.subtasks or []
    all_done = len(subtasks) > 0 and state.next_subtask_index >= len(subtasks)

    system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's work based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user.
    For replan_needed: TRUE only if all subtasks are done, criteria NOT met, and a different plan might help."""

    user_message = f"""You are evaluating the work done by the Assistant. You decide what action to take based on the results.

    The conversation and work so far:
    {format_conversation((state.messages or [])[-10:])}

    The success criteria for this assignment is:
    {state.success_criteria}

    The task results are:
    {chr(10).join(f"    - {r}" for r in (state.subtask_results or []))}

    All subtasks completed: {all_done}

    Respond with your feedback, and decide if the success criteria is met.
    Also, decide if more user input is required, or if replanning might help.
    """

    evaluator_messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]
    response: EvaluatorOutput = llm_with_output.invoke(evaluator_messages)

    replan = (
        response.replan_needed
        and all_done
        and not response.user_input_needed
        and len(subtasks) > 0
    )

    from langchain_core.messages import AIMessage

    return {
        "feedback_on_work": response.feedback,
        "success_criteria_met": response.success_criteria_met,
        "user_input_needed": response.user_input_needed,
        "replan_needed": replan,
        "messages": [AIMessage(content=f"Evaluator: {response.feedback}")],
    }
