from schema import ClarifierOutput, State, ClarifierStateDiff
from utils.utils import dict_to_aimessage, format_conversation
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_core.language_models import LanguageModelInput
from langchain_openai.chat_models.base import _DictOrPydantic
from datetime import datetime


def clarifier_agent(
    llm_with_output: Runnable[LanguageModelInput, _DictOrPydantic],
    state: State
) -> dict:

    system_message = f"""
You are the CLARIFIER agent in a LangGraph-based multi-agent system.

WHEN YOU ARE CALLED:
You are invoked in one of two situations:

1) The user has just submitted a request, and the system must determine
   whether the request is sufficiently clear to proceed.

2) A previous Evaluator agent has DENIED an otherwise sensible task produced
   by the Executor agent. In this case:
   - The denial reason is stated in the evaluator's feedback.
   - The system requires user clarification, correction, or confirmation.

YOUR GOAL:
Determine whether the system needs additional input from the USER
in order to proceed safely and correctly.

WHAT YOU MUST DO:
- If additional user input IS REQUIRED:
    - Ask exactly ONE clear, specific question directed to the user
    - Set user_input_needed = true
- If additional user input IS NOT REQUIRED:
    - Do NOT ask any question
    - Do NOT emit any assistant message
    - Set user_input_needed = false

IMPORTANT CONSTRAINTS:
- You must consider the FULL conversation history.
- If side effects are currently requested:
    - You must give GREATER WEIGHT to the evaluator's feedback.
- Do NOT repeat previous assistant questions.
- Do NOT ask for information the user already provided.
- Do NOT acknowledge, summarize, or restate the request unless a question
  is strictly required.

SIDE EFFECT CONSENT EXTRACTION:
- If side effects are currently requested:
    - You MUST check which side effect the system requested and whether the user’s LATEST message provides explicit consent for it:
        - Explicit approval (e.g. "yes, go ahead", "I approve"):
            → set user_side_effects_confirmed = true
        - Explicit refusal or revocation:
            → set user_side_effects_confirmed = false
        - If the user has not addressed side effects:
            → omit user_side_effects_confirmed entirely
        - If consent is extracted:
            → Set user_input_needed = false.
            → Do NOT ask a question.
            → Include the extracted user_side_effects_confirmed.

OUTPUT RULES:
- The field `messages` represents updates to LangGraph state.messages.
- If you include `messages`, it MUST be a LIST of message OBJECTS.
- Each message object MUST have EXACTLY this structure:
{{
  "role": "assistant",
  "content": "<question>"
}}
- If user_input_needed = true:
    - You MUST include `messages`
    - `messages` MUST be a list with EXACTLY ONE object
    - That object MUST have:
        - "role": "assistant"
        - "content": the question text
    - You MUST NOT output a string, number, or object directly for `messages`
- If user_input_needed = false:
    - You MUST NOT include `messages` at all
    - Do NOT output an empty list
    - Do NOT output null

CURRENT CONTEXT:
- Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    last_user_message = next(
        (m for m in reversed(state.messages) if isinstance(m, HumanMessage)),
        None,
    )

    last_user_input = (
        last_user_message.content if last_user_message else "(no user message)"
    )

    human_message = f"""
[CONVERSATION HISTORY]
{format_conversation(state.messages)}

[LATEST USER MESSAGE]
"{last_user_input}"

[SYSTEM STATE]
- Side effects currently requested: {state.side_effects_requested}
- Evaluator feedback: {state.feedback_on_work or "(none)"}

[TASK]
1. Analyze user intent.
2. Extract side effect consent if applicable.
3. Decide if user input is needed.
"""

    llm_response: ClarifierOutput  = llm_with_output.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content=human_message)
    ])

    diff: ClarifierStateDiff = llm_response.state_diff

    updates: dict = {}

    if diff.messages:
        updates["messages"] = [dict_to_aimessage(m) for m in diff.messages]

    if diff.user_input_needed is not None:
        updates["user_input_needed"] = bool(diff.user_input_needed)

    if diff.user_side_effects_confirmed is not None:
        updates["user_side_effects_confirmed"] = bool(diff.user_side_effects_confirmed)

    return updates
