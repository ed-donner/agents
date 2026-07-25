from schema import State, FinalizerOutput
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.language_models import LanguageModelInput
from langchain_openai.chat_models.base import _DictOrPydantic
from utils.utils import dict_to_aimessage


def finalizer_agent(
    llm_with_output: Runnable[LanguageModelInput, _DictOrPydantic],
    state: State
) -> dict:

    system_msg = f"""
You are the FINALIZER agent in a multi-agent system.

ROLE:
Produce the FINAL, user-facing response once the system
has reached a TERMINAL state.

TERMINAL STATES INCLUDE:
- Successful task completion
- Task cancellation or refusal by the user
- Task halted because required approval was not granted
- Task could not be completed

IMPORTANT RULES (STRICT):
- Do NOT ask questions.
- Do NOT request approval or confirmation.
- Do NOT infer missing intent.
- Do NOT mention internal agents or system mechanics.
- Do NOT reopen the task.

INTERPRETING SIDE EFFECT CONSENT:
- Explicit approval → user_side_effects_confirmed = true
- Explicit refusal → user_side_effects_confirmed = false
- Not present (None) → user did not address side effects

You must respect the meaning of these states exactly as given.

TONE:
Clear, respectful, professional, human.
"""

    human_msg = f"""
FINAL SYSTEM STATE (AUTHORITATIVE):

Plan:
{state.plan or "(none)"}

Success criteria:
{state.success_criteria or "(none)"}

Subtask results:
{chr(10).join(f"- {r}" for r in state.subtask_results) or "(none)"}

Success criteria met:
{state.success_criteria_met}

User side effects consent:
{state.user_side_effects_confirmed if state.user_side_effects_confirmed is not None else "Not provided"}

Evaluator feedback:
{state.feedback_on_work or "(none)"}

INSTRUCTIONS:
Generate the final message to the user based strictly on the state above.

- If success_criteria_met is TRUE:
    → Summarize the successful outcome.

- If success_criteria_met is FALSE AND user_side_effects_confirmed is FALSE:
    → Acknowledge the user's decision to decline and explain the task will not proceed.

- If success_criteria_met is FALSE AND user_side_effects_confirmed is None:
    → Explain that the task did not proceed because required approval was not provided.

- Otherwise:
    → Clearly explain why the task could not be completed.

This is the FINAL message.
"""

    llm_response: FinalizerOutput = llm_with_output.invoke([
        SystemMessage(content=system_msg),
        HumanMessage(content=human_msg)
    ])

    return {
        "messages": [dict_to_aimessage(llm_response.final_answer)],
        "final_answer": llm_response.final_answer
    }
