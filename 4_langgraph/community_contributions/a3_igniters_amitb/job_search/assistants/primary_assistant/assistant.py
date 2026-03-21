from typing import Any, Dict

from langchain_core.messages import SystemMessage

from primary_assistant.prompts import (
    SYSTEM_PROMPT as primary_assistant_prompt,
    FEEDBACK_PROMPT as feedback_prompt
)
from config import get_llm, PRIMARY_ASSISTANT
from state import State
from tools import add_tools


async def primary_assistant(state: State, **kwargs) -> Dict[str, Any]:
    """
    The primary assistant is the main assistant that routes the task to the
    appropriate sub-assistant.
    Args:
        llm: The LLM to use for the primary assistant
        state: The state of the primary assistant

    Returns:
        The updated state of the primary assistant
    """
    system_message = primary_assistant_prompt

    if state.get("feedback"):
        system_message += feedback_prompt.format(feedback=state["feedback"])

    # Add in the system message
    found_system_message = False
    messages = state["messages"]
    for message in messages:
        if isinstance(message, SystemMessage):
            message.content = system_message
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=system_message)] + messages

    # Invoke the LLM with tools
    _tools = await add_tools()
    llm = get_llm(**kwargs).bind_tools(_tools)

    response = llm.invoke(messages)

    # Return updated state
    return {
        "messages": [response],
        "last_assistant": PRIMARY_ASSISTANT,
    }
