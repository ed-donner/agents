from pydantic import BaseModel, Field
from agents import Agent
from typing import List

print("🔧 [MATCHER AGENT] Job matcher agent module loaded")

INSTRUCTIONS = (
    "You are an expert job fit analyzer. "
    "Given a candidate's resume and a list of job postings, evaluate how well the candidate matches each job. "
    "For each job, provide: "
    "1) A match score from 0-100 based on skills, experience, and requirements fit. "
    "2) Top 3 candidate strengths relevant to this job. "
    "3) Up to 2 potential gaps between the candidate and job requirements. "
    "4) Brief talking points (2-3) to emphasize in an application. "
    "Focus on concrete, specific matches between skills and requirements. "
    "Be honest but optimistic in assessments. "
    "For jobs with less than 60% match, note this as a 'low match' in comments."
)


class JobMatch(BaseModel):
    """Represents a single job match analysis"""
    job_title: str = Field(description="Title of the job being matched")
    company_name: str = Field(description="Company offering the position")
    match_score: int = Field(description="Match score from 0-100", ge=0, le=100)
    key_strengths: List[str] = Field(description="Top 3 candidate strengths for this job")
    potential_gaps: List[str] = Field(description="Up to 2 skill/experience gaps for this position")
    talking_points: List[str] = Field(description="2-3 points to emphasize in application")
    comments: str = Field(description="Additional insights or recommendations")


class JobMatchResults(BaseModel):
    """Collection of job match analyses"""
    matches: List[JobMatch] = Field(description="List of job match analyses")
    best_match_index: int = Field(description="Index of the best overall match")
    summary: str = Field(description="Brief summary of overall match findings")


print("🔧 [MATCHER AGENT] Initializing job matcher agent...")
matcher_agent = Agent(
    name="JobMatcherAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=JobMatchResults,
)
print("✅ [MATCHER AGENT] Job matcher agent initialized successfully")