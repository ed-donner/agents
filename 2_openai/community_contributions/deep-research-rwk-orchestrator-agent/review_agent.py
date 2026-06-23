from pydantic import BaseModel, Field
from agents import Agent
import parameters as param


class ReviewResult(BaseModel):
    is_acceptable: bool = Field(description="Is the report acceptable? True or False.")
    feedback: list[str] = Field(description="Criticisms of the report.")


review_agent = Agent[ReviewResult](
    name="ReviewAgent",
    instructions= param.INSTRUCTIONS_REVIEW,
    model= param.MODEL_REVIEW,
    output_type=ReviewResult,
)
