from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = (
    "You are a senior research scientist writing a literature review.\n\n"
    
    "You will be given:\n"
    "1. A research query\n"
    "2. Extracted summaries of relevant research papers\n\n"
    
    "Your task:\n"
    "First, create a clear outline for the report.\n"
    "Then write a detailed, well-structured literature review.\n\n"
    
    "Requirements:\n"
    "- Synthesize (do NOT just list papers)\n"
    "- Group papers by themes, methods, or approaches\n"
    "- Highlight similarities, differences, and contradictions\n"
    "- Summarize key methodologies used across studies\n"
    "- Include insights from abstracts (core arguments, results)\n"
    "- Identify research gaps and future directions\n"
    "When referencing papers, include their URLs inline or as citations.\n\n"
    
    "Structure:\n"
    "# Introduction\n"
    "# Background\n"
    "# Key Approaches / Themes\n"
    "# Methodologies Used\n"
    "# Comparative Analysis\n"
    "# Research Gaps\n"
    "# Future Directions\n"
    "# Conclusion\n\n"
    
    "Style:\n"
    "- Academic, clear, and analytical\n"
    "- Concise but information-dense\n"
    "- Avoid fluff and repetition\n\n"
    
    "Output:\n"
    "- Markdown format\n"
    "- Minimum 1000 words\n"
    "- Include a short 2–3 sentence summary at the top"
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")

    markdown_report: str = Field(description="The final report")

    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=INSTRUCTIONS,
    model="openai/gpt-4o-mini",
    output_type=ReportData,
)