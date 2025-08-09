from pydantic import BaseModel, Field
from agents import Agent
from typing import List

print("🔧 [RESUME PARSER] Resume parser agent module loaded")

INSTRUCTIONS = (
    "You are an expert resume analyzer. "
    "Given the text content of a resume, extract and identify the most important information for job searching. "
    "Focus on: "
    "1) Technical skills and technologies mentioned "
    "2) Years of experience (estimate if not explicitly stated) "
    "3) Job titles and roles held "
    "4) Industries or domains worked in "
    "5) Education level and relevant degrees "
    "6) Key achievements or notable projects "
    "Be thorough but concise. Extract only factual information present in the resume text."
)

class ResumeProfile(BaseModel):
    """Structured resume information extracted by AI"""
    technical_skills: List[str] = Field(description="Programming languages, frameworks, tools, technologies")
    years_experience: str = Field(description="Estimated total years of professional experience")
    job_titles: List[str] = Field(description="Previous job titles or roles")
    industries: List[str] = Field(description="Industries or business domains worked in")
    education: str = Field(description="Highest education level and relevant degrees")
    key_achievements: List[str] = Field(description="Notable accomplishments or projects (max 3)")
    summary: str = Field(description="Brief professional summary in 2-3 sentences")

print("🔧 [RESUME PARSER] Initializing resume parser agent...")
resume_parser_agent = Agent(
    name="ResumeParserAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ResumeProfile,
)
print("✅ [RESUME PARSER] Resume parser agent initialized successfully")
