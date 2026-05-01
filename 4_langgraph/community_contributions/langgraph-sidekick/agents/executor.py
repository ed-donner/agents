from schema import State
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from utils.utils import CAPABILITIES_MANIFEST, EXECUTOR_TOOL_SAFETY, ToolSafety, infer_tool_calls
from langchain_core.runnables import Runnable
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import BaseMessage
from datetime import datetime


def executor_agent(
    llm_with_tools: Runnable[LanguageModelInput, BaseMessage],
    state: State
) -> dict:
    current = state.subtasks[state.next_subtask_index]

    system_msg = f"""
Role:
You are the EXECUTOR agent in a LangGraph-based multi-agent system.

Your responsibility is to execute the assigned subtask EXACTLY as written,
using the available tools when required.

--------------------------------------------------------------------
TOOLS
--------------------------------------------------------------------
{CAPABILITIES_MANIFEST.get("executor").get("tools")}

--------------------------------------------------------------------
TOOL USAGE GUIDELINES
--------------------------------------------------------------------

1. PARALLEL EXECUTION (ALLOWED)
- You MAY call multiple tools in a single response if the actions are independent.
- Example: Creating two different files at once.
- Example: Reading a file and listing a directory at the same time.

2. SEQUENTIAL DEPENDENCIES
- If a tool depends on the output of another (e.g., read a file, THEN modify its content),
  you MUST chain them in separate turns.
- Do NOT call dependent tools in the same parallel batch.

3. PYTHON_REPL USAGE
- You MUST explicitly print the final result.
- Example (VALID): print(math.pi * 3)
- Example (INVALID): math.pi * 3

--------------------------------------------------------------------
SAFETY & EXECUTION RULES
--------------------------------------------------------------------

4. SIDE EFFECT SAFETY
- If you need to perform irreversible actions (write/delete files, send messages):
  - Just call the tools naturally.
  - The system has a built-in safety gate that will catch your request
    and ask the user for approval if needed.
  - Do NOT ask for permission in text; just call the tool.

5. COMPLETION
- When the task is complete, produce a concise summary.
- The summary MUST be sufficient for evaluator verification.

--------------------------------------------------------------------
CURRENT CONTEXT
--------------------------------------------------------------------
- Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    human_msg = f"""
Current task:
{current.task}
"""

    if state.subtask_results:
        human_msg += f"""
Results (from previous agents):
{chr(10).join(f"- {r}" for r in state.subtask_results)}
"""

    messages = [
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ]

    for msg in state.messages:
        if isinstance(msg, (AIMessage, ToolMessage)):
            messages.append(msg)

    llm_response = llm_with_tools.invoke(messages)

    if llm_response.tool_calls:
        tools = infer_tool_calls(llm_response)
        unsafe_tools_detected = []

        for tool in tools:
            safety = EXECUTOR_TOOL_SAFETY.get(tool.tool_name)

            is_unsafe = (
                safety == ToolSafety.IRREVERSIBLE or
                (safety == ToolSafety.SANDBOXED_COMPUTE and current.requires_side_effects)
            )

            if is_unsafe:
                unsafe_tools_detected.append(tool.tool_name)

        if unsafe_tools_detected and not state.side_effects_approved:
            unique_unsafe_names = list(set(unsafe_tools_detected))

            return {
                "side_effects_requested": True,
                "messages": [
                    AIMessage(
                        content=(
                            f"Requesting approval for side-effectful actions using tools: "
                            f"{', '.join(unique_unsafe_names)}"
                        )
                    )
                ]
            }

        return {
            "messages": [llm_response],
        }

    return {
        "subtask_results": state.subtask_results + [llm_response.content],
        "messages": [AIMessage(content=f"Execution completed for task: {current.task}")],
        "next_subtask_index": state.next_subtask_index + 1,
        "side_effects_requested": False,
        "side_effects_approved": False,
        "user_side_effects_confirmed": False
    }
