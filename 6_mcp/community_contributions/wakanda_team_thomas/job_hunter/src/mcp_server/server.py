"""
MCP Server for Job Hunter.

Provides tools for managing profiles and jobs.
Run with: uv run python -m src.mcp_server.server
"""

import sys
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_settings
from src.db.models import init_database
from src.db.repository import ProfileRepository, JobRepository
from src.schemas.profile import ProfileCreate, ProfileUpdate, Skill, Experience, Education, JobPreferences
from src.schemas.job import JobCreate, JobUpdate, MatchDetail

settings = get_settings()
SessionFactory = init_database(settings.database_url)

mcp = FastMCP("job_hunter_server")


def get_session():
    """Get a new database session."""
    return SessionFactory()


@mcp.tool()
async def create_profile(
    name: str,
    email: str,
    summary: Optional[str] = None,
    resume_path: Optional[str] = None,
) -> dict:
    """
    Create a new user profile.
    
    Args:
        name: Full name of the user
        email: Email address (must be unique)
        summary: Professional summary (optional)
        resume_path: Path to uploaded resume file (optional)
    
    Returns:
        Dictionary with profile ID and creation status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        
        existing = repo.get_by_email(email)
        if existing:
            return {
                "success": False,
                "error": f"Profile with email {email} already exists",
                "profile_id": existing.id,
            }
        
        data = ProfileCreate(
            name=name,
            email=email,
            summary=summary,
            resume_path=resume_path,
        )
        profile = repo.create(data)
        
        return {
            "success": True,
            "profile_id": profile.id,
            "message": f"Profile created for {name}",
        }
    finally:
        session.close()


@mcp.tool()
async def get_profile(profile_id: int) -> dict:
    """
    Get a profile by ID.
    
    Args:
        profile_id: The profile ID to retrieve
    
    Returns:
        Dictionary with profile data or error message
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        return {
            "success": True,
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "email": profile.email,
                "summary": profile.summary,
                "skills": profile.get_skills(),
                "experience": profile.get_experience(),
                "education": profile.get_education(),
                "keywords": profile.get_keywords(),
                "preferences": profile.get_preferences(),
                "resume_path": profile.resume_path,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            },
        }
    finally:
        session.close()


@mcp.tool()
async def update_profile_skills(profile_id: int, skills: list[dict]) -> dict:
    """
    Update the skills for a profile.
    
    Args:
        profile_id: The profile ID to update
        skills: List of skill objects with 'name', optional 'level', optional 'years'
                Example: [{"name": "Python", "level": "expert", "years": 5}]
    
    Returns:
        Dictionary with update status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        skill_objects = [Skill(**s) for s in skills]
        update_data = ProfileUpdate(skills=skill_objects)
        repo.update(profile_id, update_data)
        
        return {
            "success": True,
            "message": f"Updated {len(skills)} skills for profile {profile_id}",
            "skills_count": len(skills),
        }
    finally:
        session.close()


@mcp.tool()
async def update_profile_experience(profile_id: int, experience: list[dict]) -> dict:
    """
    Update the work experience for a profile.
    
    Args:
        profile_id: The profile ID to update
        experience: List of experience objects with 'company', 'title', optional fields
                    Example: [{"company": "Tech Corp", "title": "Senior Dev", "start_date": "2020-01"}]
    
    Returns:
        Dictionary with update status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        exp_objects = [Experience(**e) for e in experience]
        update_data = ProfileUpdate(experience=exp_objects)
        repo.update(profile_id, update_data)
        
        return {
            "success": True,
            "message": f"Updated {len(experience)} experience entries for profile {profile_id}",
            "experience_count": len(experience),
        }
    finally:
        session.close()


@mcp.tool()
async def update_profile_education(profile_id: int, education: list[dict]) -> dict:
    """
    Update the education for a profile.
    
    Args:
        profile_id: The profile ID to update
        education: List of education objects with 'institution', 'degree', optional fields
                   Example: [{"institution": "MIT", "degree": "BS Computer Science", "year": 2020}]
    
    Returns:
        Dictionary with update status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        edu_objects = [Education(**e) for e in education]
        update_data = ProfileUpdate(education=edu_objects)
        repo.update(profile_id, update_data)
        
        return {
            "success": True,
            "message": f"Updated {len(education)} education entries for profile {profile_id}",
            "education_count": len(education),
        }
    finally:
        session.close()


@mcp.tool()
async def update_profile_keywords(profile_id: int, keywords: list[str]) -> dict:
    """
    Update the keywords for a profile (used for job matching).
    
    Args:
        profile_id: The profile ID to update
        keywords: List of keywords extracted from resume
                  Example: ["python", "machine learning", "aws", "backend"]
    
    Returns:
        Dictionary with update status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        update_data = ProfileUpdate(keywords=keywords)
        repo.update(profile_id, update_data)
        
        return {
            "success": True,
            "message": f"Updated {len(keywords)} keywords for profile {profile_id}",
            "keywords_count": len(keywords),
        }
    finally:
        session.close()


@mcp.tool()
async def list_profiles() -> dict:
    """
    List all profiles in the system.
    
    Returns:
        Dictionary with list of profiles (id, name, email)
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profiles = repo.get_all()
        
        return {
            "success": True,
            "profiles": [
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email,
                }
                for p in profiles
            ],
            "total": len(profiles),
        }
    finally:
        session.close()


@mcp.tool()
async def delete_profile(profile_id: int) -> dict:
    """
    Delete a profile and all associated jobs.
    
    Args:
        profile_id: The profile ID to delete
    
    Returns:
        Dictionary with deletion status
    """
    session = get_session()
    try:
        repo = ProfileRepository(session)
        profile = repo.get_by_id(profile_id)
        
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        name = profile.name
        repo.delete(profile_id)
        
        return {
            "success": True,
            "message": f"Deleted profile for {name} and all associated jobs",
        }
    finally:
        session.close()


@mcp.tool()
async def add_job(
    profile_id: int,
    external_id: str,
    source: str,
    title: str,
    company: str,
    description: str,
    url: str,
    match_score: float,
    required_skills: Optional[list[str]] = None,
    salary_range: Optional[str] = None,
    match_details: Optional[dict] = None,
) -> dict:
    """
    Add a matched job to a profile.
    
    Args:
        profile_id: The profile ID to add the job to
        external_id: Job ID from the source board
        source: Job board source (remoteok, remotive, arbeitnow)
        title: Job title
        company: Company name
        description: Job description
        url: URL to the job posting
        match_score: Match score between 0.0 and 1.0
        required_skills: List of required skills (optional)
        salary_range: Salary range string (optional)
        match_details: Match breakdown details (optional)
    
    Returns:
        Dictionary with job ID and creation status
    """
    session = get_session()
    try:
        profile_repo = ProfileRepository(session)
        job_repo = JobRepository(session)
        
        profile = profile_repo.get_by_id(profile_id)
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        if job_repo.exists(external_id, source, profile_id):
            return {
                "success": False,
                "error": f"Job {external_id} from {source} already exists for this profile",
            }
        
        details = None
        if match_details:
            details = MatchDetail(**match_details)
        
        data = JobCreate(
            profile_id=profile_id,
            external_id=external_id,
            source=source,
            title=title,
            company=company,
            description=description,
            url=url,
            match_score=match_score,
            required_skills=required_skills or [],
            salary_range=salary_range,
            match_details=details,
        )
        job = job_repo.create(data)
        
        return {
            "success": True,
            "job_id": job.id,
            "message": f"Added job: {title} at {company}",
        }
    finally:
        session.close()


@mcp.tool()
async def get_job(job_id: int) -> dict:
    """
    Get a job by ID.
    
    Args:
        job_id: The job ID to retrieve
    
    Returns:
        Dictionary with job data or error message
    """
    session = get_session()
    try:
        repo = JobRepository(session)
        job = repo.get_by_id(job_id)
        
        if not job:
            return {
                "success": False,
                "error": f"Job {job_id} not found",
            }
        
        return {
            "success": True,
            "job": {
                "id": job.id,
                "profile_id": job.profile_id,
                "external_id": job.external_id,
                "source": job.source,
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "required_skills": job.get_required_skills(),
                "salary_range": job.salary_range,
                "url": job.url,
                "match_score": job.match_score,
                "match_details": job.get_match_details(),
                "status": job.status,
                "notes": job.notes,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "found_at": job.found_at.isoformat() if job.found_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            },
        }
    finally:
        session.close()


@mcp.tool()
async def list_jobs(
    profile_id: int,
    status: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 50,
) -> dict:
    """
    List jobs for a profile with optional filters.
    
    Args:
        profile_id: The profile ID to list jobs for
        status: Filter by status (new, reviewing, applied, interview, rejected, accepted)
        min_score: Minimum match score filter (0.0-1.0)
        limit: Maximum number of jobs to return
    
    Returns:
        Dictionary with list of jobs
    """
    session = get_session()
    try:
        repo = JobRepository(session)
        jobs = repo.get_by_profile(
            profile_id=profile_id,
            status=status,
            min_score=min_score,
            limit=limit,
        )
        
        return {
            "success": True,
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company,
                    "source": j.source,
                    "match_score": j.match_score,
                    "status": j.status,
                    "url": j.url,
                    "found_at": j.found_at.isoformat() if j.found_at else None,
                }
                for j in jobs
            ],
            "total": len(jobs),
        }
    finally:
        session.close()


@mcp.tool()
async def update_job_status(
    job_id: int,
    status: str,
    notes: Optional[str] = None,
) -> dict:
    """
    Update the status of a job application.
    
    Args:
        job_id: The job ID to update
        status: New status (new, reviewing, applied, interview, rejected, accepted)
        notes: Optional notes about the status change
    
    Returns:
        Dictionary with update status
    """
    session = get_session()
    try:
        repo = JobRepository(session)
        job = repo.get_by_id(job_id)
        
        if not job:
            return {
                "success": False,
                "error": f"Job {job_id} not found",
            }
        
        valid_statuses = ["new", "reviewing", "applied", "interview", "rejected", "accepted"]
        if status not in valid_statuses:
            return {
                "success": False,
                "error": f"Invalid status. Must be one of: {valid_statuses}",
            }
        
        update_data = JobUpdate(status=status, notes=notes)
        repo.update(job_id, update_data)
        
        return {
            "success": True,
            "message": f"Updated job {job_id} status to {status}",
            "job_id": job_id,
            "status": status,
        }
    finally:
        session.close()


@mcp.tool()
async def delete_job(job_id: int) -> dict:
    """
    Delete a job from the list.
    
    Args:
        job_id: The job ID to delete
    
    Returns:
        Dictionary with deletion status
    """
    session = get_session()
    try:
        repo = JobRepository(session)
        job = repo.get_by_id(job_id)
        
        if not job:
            return {
                "success": False,
                "error": f"Job {job_id} not found",
            }
        
        title = job.title
        repo.delete(job_id)
        
        return {
            "success": True,
            "message": f"Deleted job: {title}",
        }
    finally:
        session.close()


@mcp.tool()
async def get_job_stats(profile_id: int) -> dict:
    """
    Get job statistics for a profile.
    
    Args:
        profile_id: The profile ID to get stats for
    
    Returns:
        Dictionary with job statistics
    """
    session = get_session()
    try:
        profile_repo = ProfileRepository(session)
        job_repo = JobRepository(session)
        
        profile = profile_repo.get_by_id(profile_id)
        if not profile:
            return {
                "success": False,
                "error": f"Profile {profile_id} not found",
            }
        
        stats = job_repo.get_stats(profile_id)
        
        return {
            "success": True,
            "stats": {
                "total_jobs": stats.total_jobs,
                "new_jobs": stats.new_jobs,
                "reviewing_jobs": stats.reviewing_jobs,
                "applied_jobs": stats.applied_jobs,
                "interview_jobs": stats.interview_jobs,
                "rejected_jobs": stats.rejected_jobs,
                "accepted_jobs": stats.accepted_jobs,
                "avg_match_score": stats.avg_match_score,
            },
        }
    finally:
        session.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
