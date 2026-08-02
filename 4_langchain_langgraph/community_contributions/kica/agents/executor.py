from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import Runnable

from schema import State


def executor_agent(llm_with_tools: Runnable, state: State) -> dict[str, Any]:
    subtasks = state.subtasks or []
    idx = state.next_subtask_index

    if not subtasks or idx >= len(subtasks):
        return {"messages": [AIMessage(content="No executor task.")]}

    current = subtasks[idx]
    if current.assigned_to != "executor":
        return {"messages": [AIMessage(content=f"Task assigned to {current.assigned_to}.")]}

    system_message = f"""You are the EXECUTOR agent. Use tools to perform actions.
    You have a Python REPL (use print() for output), file read/write/list/copy/move/delete, and push notification.
    When done, summarize what you did. Do NOT call tools after your final summary.
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is your task:
    {current.task}
    """

    results = state.subtask_results or []
    if results:
        system_message += f"""
    Previously completed results:
    {chr(10).join(f"    - {r}" for r in results)}
    """

    msgs = [SystemMessage(content=system_message)]
    for m in state.messages or []:
        if isinstance(m, (AIMessage, ToolMessage)):
            msgs.append(m)
    msgs.append(HumanMessage(content=f"Complete this task: {current.task}"))

    response = llm_with_tools.invoke(msgs)

    if hasattr(response, "tool_calls") and response.tool_calls:
        return {"messages": [response]}

    content = getattr(response, "content", "") or ""
    summary = f"Executed: {content[:200]}..." if len(content) > 200 else f"Executed: {content}"
    return {
        "subtask_results": results + [content],
        "next_subtask_index": idx + 1,
        "messages": [AIMessage(content=summary)],
    }
