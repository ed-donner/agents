from schema import State, EvaluatorOutput
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import Runnable
from langchain_core.language_models import LanguageModelInput
from langchain_openai.chat_models.base import _DictOrPydantic
from utils.utils import dict_to_aimessage, format_conversation
from datetime import datetime


def evaluator_agent(
    llm_with_output: Runnable[LanguageModelInput, _DictOrPydantic],
    state: State
) -> dict:

    total_subtasks = len(state.subtasks or [])
    tasks_remaining = state.next_subtask_index < total_subtasks
    all_tasks_done = total_subtasks > 0 and not tasks_remaining

    system_message = f"""
Role:
You are the EVALUATOR agent in a LangGraph-based multi-agent system.

Your role is to produce structured judgments about SAFETY and QUALITY.
You do NOT execute actions, suggest plans, or decide control flow.

You MUST make THREE INDEPENDENT evaluations:

────────────────────────────────────
DECISION A — SAFETY (Side Effects Approval)
────────────────────────────────────
Goal:
Determine whether the requested side effects are ALLOWED IN PRINCIPLE.

Context:
- The system pauses execution if ANY tool in a parallel batch requires approval.
- Look at the [PENDING REQUEST] section to see which tools are being requested.

Rules:
- side_effects_approved:
  - TRUE → Side effects are safe and policy-compliant (or explicitly approved by user).
  - FALSE → Side effects violate a clear policy or safety rule, OR user approval is missing.

Constraints:
- If NO side effects were requested:
  - side_effects_approved MUST be FALSE (default).
- If side effects WERE requested:
  - You MUST check if the user has provided explicit consent in the conversation history.
  - If `user_side_effects_confirmed` is TRUE in the state, you generally approve.
  - If `user_side_effects_confirmed` is FALSE/None, you MUST block (approve=False) and request user input.

────────────────────────────────────
DECISION B — QUALITY (Success Criteria)
────────────────────────────────────
Goal:
Determine whether the task outputs meet the success criteria.

Rules:
- success_criteria_met:
  - TRUE → All required information is correct and complete.
  - FALSE → Any required element is missing, incorrect, or ambiguous.

- user_input_needed:
  - TRUE → Progress is blocked by missing or unclear user information (including missing approval).
  - FALSE → The system can continue autonomously.

Blocking Rule:
If side effects are requested AND side_effects_approved is FALSE:
- success_criteria_met MUST be FALSE
- user_input_needed MUST be TRUE (to trigger the interaction loop)

────────────────────────────────────
DECISION C — REPLANNING NEED
────────────────────────────────────
Goal:
Determine whether the system SHOULD attempt to fix its own work.

Rules:
- replan_needed:
  - TRUE → The system could reasonably fix the issue autonomously.
  - FALSE → Replanning would not help or user input is required.

IMPORTANT:
- If any subtasks remain, replan_needed MUST be FALSE.
- If user_input_needed is TRUE, replan_needed MUST be FALSE.

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    recent_context = format_conversation(state.messages[-3:]) or "(none)"

    human_msg = f"""
[EXECUTION STATUS]
Total subtasks: {total_subtasks}
Next subtask index: {state.next_subtask_index}
All subtasks completed: {all_tasks_done}

[SUCCESS CRITERIA]
{state.success_criteria}

[TASK RESULTS]
{chr(10).join(f"- {r}" for r in state.subtask_results)}

[PENDING REQUEST / RECENT CONTEXT]
{recent_context}

[SAFETY CONTEXT]
Side effects requested: {state.side_effects_requested}
User explicitly approved side effects: {state.user_side_effects_confirmed}
"""

    llm_response: EvaluatorOutput = llm_with_output.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content=human_msg)
    ])

    approval_blocked = (
        state.side_effects_requested
        and not llm_response.side_effects_approved
    )

    user_input_needed = llm_response.user_input_needed
    if tasks_remaining and not approval_blocked:
        user_input_needed = False

    replan_needed = (
      llm_response.replan_needed
      and all_tasks_done
      and not user_input_needed
    )

    updates = {
        "messages": [dict_to_aimessage(llm_response.feedback)],
        "feedback_on_work": llm_response.feedback,
        "success_criteria_met": llm_response.success_criteria_met,
        "user_input_needed": user_input_needed,
        "replan_needed": replan_needed
    }

    if state.side_effects_requested:
        updates["side_effects_approved"] = llm_response.side_effects_approved

    return updates
