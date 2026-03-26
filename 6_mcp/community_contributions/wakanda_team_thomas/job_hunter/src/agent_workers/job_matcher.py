"""
Job Matcher Agent.

Evaluates job listings against a profile and saves matching jobs.
Uses hybrid approach: rule-based scoring + LLM semantic analysis.
"""

from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent, function_tool

from src.db.models import init_database
from src.db.repository import ProfileRepository, JobRepository
from src.schemas.job import JobCreate
from src.config import get_settings, JobSource
from src.utils.scoring import calculate_match_score, MatchResult


class MatchedJob(BaseModel):
    """A job that matches the profile criteria."""
    job_id: int = Field(description="Database ID of the saved job")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    match_score: float = Field(description="Overall match score (0-1)")
    match_explanation: str = Field(description="Why this job matches the profile")


class MatchingResult(BaseModel):
    """Result of the job matching operation."""
    total_evaluated: int = Field(description="Total jobs evaluated")
    total_matched: int = Field(description="Jobs meeting threshold")
    matched_jobs: list[MatchedJob] = Field(default_factory=list, description="List of matched jobs")
    skipped_count: int = Field(default=0, description="Jobs skipped (below threshold or duplicates)")


settings = get_settings()
SessionFactory = init_database(settings.database_url)


def _get_repositories():
    """Get repository instances."""
    session = SessionFactory()
    return ProfileRepository(session), JobRepository(session)


@function_tool
def get_profile_data(profile_id: int) -> str:
    """
    Get profile data for matching.
    
    Args:
        profile_id: ID of the profile
        
    Returns:
        JSON string with profile skills, keywords, and experience
    """
    import json
    
    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    data = {
        "id": profile.id,
        "name": profile.name,
        "skills": profile.get_skills(),
        "keywords": profile.get_keywords(),
        "experience": profile.get_experience(),
        "summary": profile.summary,
    }
    return json.dumps(data)


@function_tool
def calculate_job_match(profile_id: int, job_json: str) -> str:
    """
    Calculate match score between a profile and a job listing.
    Uses rule-based scoring for fast pre-filtering.
    
    Args:
        profile_id: ID of the profile
        job_json: JSON string with job data (title, company, description, required_skills)
        
    Returns:
        JSON with match score and component scores
    """
    import json
    
    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    try:
        job_data = json.loads(job_json)
    except json.JSONDecodeError as e:
        return f"error:Invalid job JSON: {e}"
    
    profile_skills = profile.get_skills()
    profile_keywords = profile.get_keywords()
    profile_experience = profile.get_experience()
    
    job_skills = job_data.get("required_skills", [])
    job_title = job_data.get("title", "")
    job_description = job_data.get("description", "")
    
    result = calculate_match_score(
        profile_skills=profile_skills,
        profile_experience=profile_experience,
        profile_keywords=profile_keywords,
        job_title=job_title,
        job_description=job_description,
        job_required_skills=job_skills,
    )
    
    return json.dumps({
        "overall_score": result.score,
        "skills_score": result.skills_score,
        "experience_score": result.experience_score,
        "keywords_score": result.keywords_score,
        "requirements_score": result.requirements_score,
        "meets_threshold": result.meets_threshold,
    })


@function_tool
def check_job_exists(external_id: str, source: str, profile_id: int) -> str:
    """
    Check if a job already exists in the database for this profile.
    
    Args:
        external_id: External ID of the job from the job board
        source: Source job board name
        profile_id: Profile ID
        
    Returns:
        "exists" or "not_found"
    """
    _, job_repo = _get_repositories()
    
    if job_repo.exists(external_id, source, profile_id):
        return "exists"
    return "not_found"


@function_tool
def save_matched_job(
    profile_id: int,
    external_id: str,
    source: str,
    title: str,
    company: str,
    description: str,
    url: str,
    match_score: float,
    required_skills: list[str],
    match_explanation: str,
    location: Optional[str] = None,
    salary_range: Optional[str] = None,
) -> str:
    """
    Save a matched job to the database.
    
    Args:
        profile_id: Profile ID
        external_id: External job ID from the board
        source: Job board source (remoteok, remotive, arbeitnow)
        title: Job title
        company: Company name
        description: Job description
        url: Application URL
        match_score: Calculated match score (0-1)
        required_skills: List of required skills
        match_explanation: LLM-generated explanation of why this matches
        location: Job location (optional)
        salary_range: Salary range if available (optional)
        
    Returns:
        "saved:id=<job_id>" or "error:<message>"
    """
    _, job_repo = _get_repositories()
    
    if job_repo.exists(external_id, source, profile_id):
        return f"error:Job already exists for this profile"
    
    valid_sources = [s.value for s in JobSource]
    if source.lower() not in valid_sources:
        source = "other"
    
    try:
        job_data = JobCreate(
            profile_id=profile_id,
            external_id=external_id,
            source=source.lower(),
            title=title,
            company=company,
            description=description[:2000] if description else "",
            url=url,
            location=location,
            salary_range=salary_range,
            match_score=match_score,
            required_skills=required_skills,
            match_details=[{
                "component": "llm_analysis",
                "score": match_score,
                "explanation": match_explanation,
            }],
        )
        job = job_repo.create(job_data)
        return f"saved:id={job.id}"
    except Exception as e:
        return f"error:{str(e)}"


MATCHER_INSTRUCTIONS = """You are a job matching specialist. Your task is to evaluate job listings
against a user's profile and save matches that meet the threshold (default 60%).

For each job listing provided:

1. First check if the job already exists using check_job_exists
2. If not, calculate the match score using calculate_job_match
3. If the score meets the threshold, proceed with semantic analysis
4. Provide a detailed explanation of why this job matches the profile:
   - Which skills align
   - Relevant experience
   - Why this role would be good for the candidate
5. Save the matched job using save_matched_job with your explanation

When analyzing matches, consider:
- Direct skill matches (exact technologies)
- Related skill matches (e.g., React experience is relevant for frontend roles)
- Experience level alignment (junior vs senior roles)
- Domain expertise (fintech, healthcare, etc.)

Save all jobs that meet the threshold. Balance quality with opportunity.

Return a MatchingResult with counts and details of matched jobs."""


job_matcher_agent = Agent(
    name="JobMatcherAgent",
    instructions=MATCHER_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[
        get_profile_data,
        calculate_job_match,
        check_job_exists,
        save_matched_job,
    ],
    output_type=MatchingResult,
)


async def match_jobs(profile_id: int, jobs: list[dict]) -> MatchingResult:
    """
    Match a list of jobs against a profile and save matches.
    
    Args:
        profile_id: ID of the profile to match against
        jobs: List of job dictionaries from job search
        
    Returns:
        MatchingResult with matched jobs
    """
    from agents import Runner
    import json
    
    result = await Runner.run(
        job_matcher_agent,
        f"Evaluate these jobs for profile {profile_id} and save matches that meet the threshold:\n{json.dumps(jobs)}",
    )
    
    return result.final_output_as(MatchingResult)


def match_jobs_fast(profile_id: int, jobs: list[dict], threshold: float = 0.6) -> list[dict]:
    """
    Fast rule-based matching without LLM (for pre-filtering).
    
    Args:
        profile_id: Profile ID
        jobs: List of job dictionaries
        threshold: Minimum match score (default 0.6)
        
    Returns:
        List of jobs meeting the threshold
    """
    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    
    if not profile:
        return []
    
    profile_skills = profile.get_skills()
    profile_keywords = profile.get_keywords()
    profile_experience = profile.get_experience()
    
    matched = []
    for job in jobs:
        result = calculate_match_score(
            profile_skills=profile_skills,
            profile_experience=profile_experience,
            profile_keywords=profile_keywords,
            job_title=job.get("title", ""),
            job_description=job.get("description", ""),
            job_required_skills=job.get("required_skills", []),
        )
        
        if result.score >= threshold:
            job["match_score"] = result.score
            job["match_details"] = {
                "skills": result.skills_score,
                "experience": result.experience_score,
                "keywords": result.keywords_score,
                "requirements": result.requirements_score,
            }
            matched.append(job)
    
    return sorted(matched, key=lambda x: x["match_score"], reverse=True)
