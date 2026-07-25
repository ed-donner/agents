from pydantic import BaseModel, Field
from agents import Agent
import parameters as param


# structure of output, 3 fields with descriptions
class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent[ReportData](
    name="WriterAgent",
    instructions= param.INSTRUCTIONS_WRITER,
    model= param.MODEL_WRITER,
    output_type=ReportData,
)