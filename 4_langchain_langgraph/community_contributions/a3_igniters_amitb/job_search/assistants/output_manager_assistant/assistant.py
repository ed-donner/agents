from langchain_core.messages import SystemMessage, HumanMessage

from .prompts import SYSTEM_PROMPT, USER_PROMPT
from job_search.config import get_llm, OUTPUT_MANAGER_ASSISTANT
from job_search.state import State


def output_manager_assistant(state: State) -> State:
    last_message = state.get("executor_output") or state["messages"][-2].content

    system_message = SYSTEM_PROMPT
    user_message = USER_PROMPT.format(last_output=last_message)

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    llm = get_llm()
    response = llm.invoke(messages)

    return {
        "messages": [{"role": "assistant", "content": response.content}],
        "last_assistant": OUTPUT_MANAGER_ASSISTANT,
    }
