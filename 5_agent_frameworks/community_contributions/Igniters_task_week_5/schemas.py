from typing import List

from pydantic import BaseModel, Field


class RankedIdea(BaseModel):
    rank: int = Field(description="Overall ranking position starting from 1.")
    idea_name: str = Field(description="Short product or startup name.")
    score: float = Field(description="Overall score from 1 to 10.", ge=1, le=10)
    one_line_summary: str = Field(description="One sentence summary of the idea.")
    target_customer: str = Field(description="Primary buyer or user.")
    business_model: str = Field(description="How the idea can make money.")
    feasibility: str = Field(description="Why the MVP is realistic or difficult.")
    moat: str = Field(description="Defensible advantage if executed well.")
    key_risk: str = Field(description="Biggest execution or market risk.")
    first_mvp_step: str = Field(description="Best next practical MVP step.")


class WinningIdea(BaseModel):
    idea_name: str = Field(description="The single winning idea.")
    why_it_wins: str = Field(description="Why this idea should be built first.")
    mvp_scope: str = Field(description="A tightly scoped first version of the product.")
    target_launch_user: str = Field(description="The first user segment to pursue.")


class VentureEvaluation(BaseModel):
    executive_summary: str = Field(description="Short summary of the final recommendation.")
    ranked_ideas: List[RankedIdea] = Field(description="Ideas sorted from best to worst.")
    winning_idea: WinningIdea = Field(description="The best idea to pursue.")
    execution_plan: List[str] = Field(
        description="Three to five concrete implementation steps for the chosen idea.",
        min_length=3,
        max_length=5,
    )
