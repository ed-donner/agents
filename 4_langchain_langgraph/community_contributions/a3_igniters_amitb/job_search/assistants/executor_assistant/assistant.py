from langchain_core.messages import SystemMessage

from .prompts import SYSTEM_PROMPT
from job_search.config import get_llm, EXECUTOR_ASSISTANT
from job_search.state import State
from job_search.tools import add_tools


async def executor_assistant(state: State, tools: list) -> State:
    found_system_message = False
    messages = state["messages"]
    for message in messages:
        if isinstance(message, SystemMessage):
            message.content = SYSTEM_PROMPT
            found_system_message = True

    if not found_system_message:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    llm = get_llm().bind_tools(tools)
    response = llm.invoke(messages)

    return {
        "messages": [response],
        "last_assistant": EXECUTOR_ASSISTANT,
        "executor_output": response.content or "",
    }
