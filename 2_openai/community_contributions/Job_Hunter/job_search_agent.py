from agents import Agent, WebSearchTool, ModelSettings
from pydantic import BaseModel, Field
from typing import List, Optional

print("🔧 [SEARCH AGENT] Job search agent module loaded")

# base instructions for the agent
INSTRUCTIONS = (
    "You are a professional headhunter assistant. "
    "Given a job search term, search the web for current job postings. "
    "For each job found, produce a structured summary with the following fields only: "
    "1) Job Title, "
    "2) Company Name, "
    "3) Location, "
    "4) Salary Range (if mentioned), "
    "5) Years of Experience Required, "
    "6) Key Responsibilities (max 2 bullet points), "
    "7) Recruiter/HR Contact Email (if available), "
    "8) Job Posting URL. "
    "IMPORTANT OUTPUT GUARDRAIL: Do NOT include any jobs located in Africa, USA, or China. "
    "Filter out any positions from these regions completely. "
    "Focus on jobs in Europe, Canada, Australia, and other regions outside the restricted areas. "
    "Ensure details are factual from the source. "
    "Output each job in JSON format so it can be parsed easily. "
    "Limit to 100 words per job. "
    "Do not include personal opinions, explanations, or unrelated text."
)

# Structured output for job postings
class JobPosting(BaseModel):
    job_title: str = Field(description="Title of the job position")
    company_name: str = Field(description="Name of the company offering the job")
    location: str = Field(description="Job location or remote status")
    salary_range: Optional[str] = Field(description="Salary range if mentioned")
    experience_required: Optional[str] = Field(description="Required years of experience")
    key_responsibilities: List[str] = Field(description="Max 2 bullet points on responsibilities")
    contact_email: Optional[str] = Field(description="Recruiter/HR contact email if available")
    job_url: str = Field(description="URL to the job posting")

class JobSearchResults(BaseModel):
    jobs: List[JobPosting] = Field(description="List of job postings found")

# Agent definition
print("🔧 [SEARCH AGENT] Initializing job search agent with WebSearchTool...")
search_agent = Agent(
    name="Job Search Agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
    output_type=JobSearchResults,
)
print("✅ [SEARCH AGENT] Job search agent initialized successfully")
