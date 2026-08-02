from schema import State
from utils.utils import dict_to_aimessage
from langchain_core.messages import HumanMessage, SystemMessage


def summarizer_agent(llm, state: State) -> dict:

    current = state.subtasks[state.next_subtask_index]

    system_msg = f"""
Role:
You are the SUMMARIZER agent in a LangGraph-based multi-agent system.

Task:
- From the previous agents results, synthetize a report.

Results (from previous agents):
{chr(10).join(f"- {r}" for r in state.subtask_results)}

Rules:
- Capture the main points.
- Do not introduce new information.
- Do not include any additional commentary other than the report itself.
"""

    human_msg = f"Task:\n{current.task}"

    llm_response = llm.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ])

    return {
        "subtask_results": state.subtask_results + [llm_response.content],
        "messages": [dict_to_aimessage(llm_response)],
        "next_subtask_index": state.next_subtask_index + 1
    }
