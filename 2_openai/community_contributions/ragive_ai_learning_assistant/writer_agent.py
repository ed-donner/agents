from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior learning designer tasked with producing a detailed, structured learning roadmap. "
    "You will receive the learner's goal, profile constraints, a structured skill plan with week ranges, "
    "and curated resources for each skill. Your job is to synthesize all of this into a professional markdown roadmap.\n\n"
    "The roadmap must follow this structure:\n"
    "- A top-level heading with the goal title\n"
    "- A short motivational introduction (2-3 sentences)\n"
    "- A Learner Profile section summarizing available hours/week, budget, prior experience, and preferred learning style\n"
    "- Phases grouped by logical skill clusters, each with:\n"
    "  - Week range\n"
    "  - Skills covered\n"
    "  - Subskills as bullet points\n"
    "  - Resources section\n"
    "  - A milestone or checkpoint\n"
    "- A Final Project section\n"
    "- A Tips and Study Habits section with 4-5 actionable tips\n"
    "- A Delivery Notes section explaining how the roadmap export should be used for the requested destination\n\n"
    "Adapt the pacing and wording to the learner profile. "
    "Use clean markdown. Be thorough and detailed. Aim for 1000-1500 words minimum."
)


class RoadmapData(BaseModel):
    short_summary: str = Field(description="A 2-3 sentence summary of the learning path.")
    markdown_roadmap: str = Field(description="The full structured roadmap in markdown format.")
    follow_up_goals: list[str] = Field(description="3-4 suggested next goals after completing this roadmap.")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=RoadmapData,
)
