from pydantic import BaseModel, Field


class TopicCheckOutput(BaseModel):
    """
    The structured output from our topic-checking guardrail agent.
    """

    is_on_topic: bool = Field(
        description="True if the user's question is about Python, JavaScript, or SQL. Otherwise, False."
    )
    clarification_message: str = Field(
        description="If the question is off-topic, this is a friendly message to send back to the user."
    )
