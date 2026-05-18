from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from .prompts import SYSTEM_PROMPT, USER_PROMPT
from job_search.state import State
from job_search.config import get_llm, INPUT_GUARDRAILS_ASSISTANT


class InputGuardrails(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


def input_guardrails_assistant(state: State) -> State:
    last_message = state["messages"][-1].content

    system_message = SYSTEM_PROMPT
    user_message = USER_PROMPT.format(last_message=last_message)

    if state["feedback"]:
        user_message += (
            "Also, note that in a prior attempt from the Assistant, you"
            f" provided this feedback: {state['feedback']}\n. If you're seeing"
            " the Assistant repeating the same mistakes, then consider"
            " responding that user input is required."
        )

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    llm = get_llm().with_structured_output(InputGuardrails)
    response = llm.invoke(messages)

    new_state = {
        "messages": [
            {
                "role": "assistant",
                "content": f"Input guardrails feedback on this message: {response.feedback}",
            }
        ],
        "feedback": response.feedback,
        "success_criteria_met": response.success_criteria_met,
        "user_input_needed": response.user_input_needed,
        "last_assistant": INPUT_GUARDRAILS_ASSISTANT
    }
    return new_state
