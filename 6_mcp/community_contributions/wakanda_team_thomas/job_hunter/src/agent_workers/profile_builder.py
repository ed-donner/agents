"""
Profile Builder Agent.

Takes parsed resume data and creates/updates a profile in the database.
"""

from typing import Optional
from pydantic import BaseModel, Field

from agents import Agent, function_tool

from src.db.models import init_database
from src.db.repository import ProfileRepository
from src.schemas.profile import ProfileCreate, ProfileUpdate, Skill, Experience, Education
from src.config import get_settings
from src.agent_workers.resume_parser import ParsedResume


class ProfileBuildResult(BaseModel):
    """Result of profile building operation."""
    success: bool = Field(description="Whether the profile was created/updated successfully")
    profile_id: Optional[int] = Field(default=None, description="ID of the created/updated profile")
    message: str = Field(description="Status message describing what was done")
    is_new: bool = Field(default=False, description="True if a new profile was created")


settings = get_settings()
SessionFactory = init_database(settings.database_url)


def _get_repository() -> ProfileRepository:
    """Get a new profile repository instance."""
    session = SessionFactory()
    return ProfileRepository(session)


@function_tool
def check_existing_profile(email: str) -> str:
    """
    Check if a profile with the given email already exists.
    
    Args:
        email: Email address to check
        
    Returns:
        JSON string with profile info if exists, or "not_found"
    """
    repo = _get_repository()
    profile = repo.get_by_email(email)
    
    if profile:
        return f"exists:id={profile.id},name={profile.name}"
    return "not_found"


@function_tool
def create_new_profile(
    name: str,
    email: str,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    summary: Optional[str] = None,
) -> str:
    """
    Create a new profile in the database.
    
    Args:
        name: Full name of the candidate
        email: Email address
        phone: Phone number (optional)
        location: Location (optional)
        summary: Professional summary (optional)
        
    Returns:
        String with result: "created:id=<profile_id>" or "error:<message>"
    """
    repo = _get_repository()
    
    existing = repo.get_by_email(email)
    if existing:
        return f"error:Profile with email {email} already exists (id={existing.id})"
    
    try:
        data = ProfileCreate(
            name=name,
            email=email,
            phone=phone,
            location=location,
            summary=summary,
        )
        profile = repo.create(data)
        return f"created:id={profile.id}"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_skills(profile_id: int, skills_json: str) -> str:
    """
    Update the skills for a profile.
    
    Args:
        profile_id: ID of the profile to update
        skills_json: JSON array of skills, each with name, level (optional), years (optional)
        
    Returns:
        "success" or "error:<message>"
    """
    import json
    
    repo = _get_repository()
    profile = repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    try:
        skills_data = json.loads(skills_json)
        skills = [Skill(**s) for s in skills_data]
        update_data = ProfileUpdate(skills=skills)
        repo.update(profile_id, update_data)
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_experience(profile_id: int, experience_json: str) -> str:
    """
    Update the work experience for a profile.
    
    Args:
        profile_id: ID of the profile to update
        experience_json: JSON array of experiences with company, title, dates, etc.
        
    Returns:
        "success" or "error:<message>"
    """
    import json
    
    repo = _get_repository()
    profile = repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    try:
        exp_data = json.loads(experience_json)
        experience = [Experience(**e) for e in exp_data]
        update_data = ProfileUpdate(experience=experience)
        repo.update(profile_id, update_data)
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_education(profile_id: int, education_json: str) -> str:
    """
    Update the education for a profile.
    
    Args:
        profile_id: ID of the profile to update
        education_json: JSON array of education entries
        
    Returns:
        "success" or "error:<message>"
    """
    import json
    
    repo = _get_repository()
    profile = repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    try:
        edu_data = json.loads(education_json)
        education = [Education(**e) for e in edu_data]
        update_data = ProfileUpdate(education=education)
        repo.update(profile_id, update_data)
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_keywords(profile_id: int, keywords: list[str]) -> str:
    """
    Update the keywords for a profile (used for job matching).
    
    Args:
        profile_id: ID of the profile to update
        keywords: List of keywords/technologies
        
    Returns:
        "success" or "error:<message>"
    """
    repo = _get_repository()
    profile = repo.get_by_id(profile_id)
    
    if not profile:
        return f"error:Profile {profile_id} not found"
    
    try:
        update_data = ProfileUpdate(keywords=keywords)
        repo.update(profile_id, update_data)
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


BUILDER_INSTRUCTIONS = """You are a profile builder agent. Your task is to take parsed resume data 
and create or update a profile in the database.

Given parsed resume data, you should:

1. First check if a profile with the same email already exists using check_existing_profile
2. If the profile exists, update it. If not, create a new one using create_new_profile
3. Update the profile with skills using update_profile_skills (pass as JSON array)
4. Update the profile with experience using update_profile_experience (pass as JSON array)
5. Update the profile with education using update_profile_education (pass as JSON array)
6. Update the profile with keywords using update_profile_keywords

When converting parsed data to the database format:
- For skills: include name, level (beginner/intermediate/advanced/expert), and years if available
- For experience: include company, title, start_date, end_date, description, location
- For education: include institution, degree, field, graduation_date
- For keywords: combine the extracted keywords with skill names and technologies mentioned

Return a ProfileBuildResult with:
- success: true if all operations completed successfully
- profile_id: the ID of the created/updated profile
- message: a summary of what was done
- is_new: true if a new profile was created, false if an existing one was updated"""


profile_builder_agent = Agent(
    name="ProfileBuilderAgent",
    instructions=BUILDER_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[
        check_existing_profile,
        create_new_profile,
        update_profile_skills,
        update_profile_experience,
        update_profile_education,
        update_profile_keywords,
    ],
    output_type=ProfileBuildResult,
)


async def build_profile(parsed_resume: ParsedResume) -> ProfileBuildResult:
    """
    Build a profile from parsed resume data.
    
    Args:
        parsed_resume: ParsedResume object from the resume parser agent
        
    Returns:
        ProfileBuildResult with the operation status
    """
    from agents import Runner
    
    result = await Runner.run(
        profile_builder_agent,
        f"Build a profile from this parsed resume data: {parsed_resume.model_dump_json()}",
    )
    
    return result.final_output_as(ProfileBuildResult)
