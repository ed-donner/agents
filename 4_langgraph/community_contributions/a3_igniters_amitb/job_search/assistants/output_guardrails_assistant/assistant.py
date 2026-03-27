from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from .prompts import SYSTEM_PROMPT, USER_PROMPT
from job_search.state import State
from job_search.config import get_llm, OUTPUT_GUARDRAILS_ASSISTANT


class OutputGuardrails(BaseModel):
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    output_filter_needed: bool = Field(description="Whether the output needs to be filtered")


def output_guardrails_assistant(state: State) -> State:
    last_message = state["messages"][-1].content

    system_message = SYSTEM_PROMPT
    user_message = USER_PROMPT.format(last_output=last_message)

    if state["feedback"]:
        user_message += (
            f"Also, note that in a prior attempt from the Assistant, you"
            f" provided this feedback: {state['feedback']}\n. If you're seeing"
            " the Assistant unable to filter the output, then provide detailed"
            " feedback as to what needs to be removed and the issue faced."
        )

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_message),
    ]

    llm = get_llm().with_structured_output(OutputGuardrails)
    response = llm.invoke(messages)

    new_state = {
        "messages": [
            {
                "role": "assistant",
                "content": f"Output guardrails feedback on this message: {response.feedback}",
            }
        ],
        "feedback": response.feedback,
        "success_criteria_met": response.success_criteria_met,
        "output_filter_needed": response.output_filter_needed,
        "last_assistant": OUTPUT_GUARDRAILS_ASSISTANT
    }
    return new_state
