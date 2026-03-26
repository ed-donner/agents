"""OpenAI agent workers consolidated into a single module."""

import asyncio
from typing import Optional

from agents import Agent, function_tool
from pydantic import BaseModel, Field

from src.config import JobSource, get_settings
from src.db.models import init_database
from src.db.repository import JobRepository, ProfileRepository
from src.job_boards import ArbeitnowClient, RemoteOKClient, RemotiveClient
from src.schemas import Education, Experience, JobCreate, ProfileCreate, ProfileUpdate, Skill
from src.utils.extractors import ExtractionError, extract_text, is_supported_file
from src.utils.scoring import calculate_match_score


class ParsedSkill(BaseModel):
    name: str = Field(description="Name of the skill")
    level: Optional[str] = Field(default=None, description="Skill level")
    years: Optional[int] = Field(default=None, description="Years of experience")


class ParsedExperience(BaseModel):
    company: str = Field(description="Company or organization name")
    title: str = Field(description="Job title or position")
    start_date: Optional[str] = Field(default=None, description="Start date in YYYY-MM or YYYY")
    end_date: Optional[str] = Field(default=None, description="End date in YYYY-MM or YYYY, or Present")
    description: Optional[str] = Field(default=None, description="Role details")
    location: Optional[str] = Field(default=None, description="Job location if mentioned")


class ParsedEducation(BaseModel):
    institution: str = Field(description="School or institution")
    degree: Optional[str] = Field(default=None, description="Degree obtained")
    field: Optional[str] = Field(default=None, description="Field of study")
    graduation_date: Optional[str] = Field(default=None, description="Graduation date")


class ParsedResume(BaseModel):
    name: str = Field(description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Location")
    summary: Optional[str] = Field(default=None, description="Profile summary")
    skills: list[ParsedSkill] = Field(default_factory=list)
    experience: list[ParsedExperience] = Field(default_factory=list)
    education: list[ParsedEducation] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


def _extract_resume_text_impl(file_path: str) -> str:
    if not is_supported_file(file_path):
        return "Error: Unsupported file format. Please provide a PDF or DOCX file."
    try:
        text = extract_text(file_path)
        if not text.strip():
            return "Error: The file appears to be empty or could not be read."
        return text
    except ExtractionError as e:
        return f"Error extracting text: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@function_tool
def extract_resume_text(file_path: str) -> str:
    return _extract_resume_text_impl(file_path)


PARSER_INSTRUCTIONS = """You are a professional resume parser.
Extract structured profile data from resume text accurately."""


resume_parser_agent = Agent(
    name="ResumeParserAgent",
    instructions=PARSER_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[extract_resume_text],
    output_type=ParsedResume,
)


async def parse_resume(file_path: str) -> ParsedResume:
    from agents import Runner

    result = await Runner.run(resume_parser_agent, f"Parse the resume at: {file_path}")
    return result.final_output_as(ParsedResume)


class ProfileBuildResult(BaseModel):
    success: bool = Field(description="Whether operation succeeded")
    profile_id: Optional[int] = Field(default=None, description="Profile ID")
    message: str = Field(description="Operation summary")
    is_new: bool = Field(default=False, description="True if profile was created")


settings = get_settings()
SessionFactory = init_database(settings.database_url)


def _get_profile_repository() -> ProfileRepository:
    return ProfileRepository(SessionFactory())


@function_tool
def check_existing_profile(email: str) -> str:
    profile = _get_profile_repository().get_by_email(email)
    return f"exists:id={profile.id},name={profile.name}" if profile else "not_found"


@function_tool
def create_new_profile(
    name: str,
    email: str,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    summary: Optional[str] = None,
) -> str:
    repo = _get_profile_repository()
    existing = repo.get_by_email(email)
    if existing:
        return f"error:Profile with email {email} already exists (id={existing.id})"
    try:
        profile = repo.create(
            ProfileCreate(name=name, email=email, phone=phone, location=location, summary=summary)
        )
        return f"created:id={profile.id}"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_skills(profile_id: int, skills_json: str) -> str:
    import json

    repo = _get_profile_repository()
    if not repo.get_by_id(profile_id):
        return f"error:Profile {profile_id} not found"
    try:
        skills = [Skill(**s) for s in json.loads(skills_json)]
        repo.update(profile_id, ProfileUpdate(skills=skills))
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_experience(profile_id: int, experience_json: str) -> str:
    import json

    repo = _get_profile_repository()
    if not repo.get_by_id(profile_id):
        return f"error:Profile {profile_id} not found"
    try:
        experience = [Experience(**e) for e in json.loads(experience_json)]
        repo.update(profile_id, ProfileUpdate(experience=experience))
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_education(profile_id: int, education_json: str) -> str:
    import json

    repo = _get_profile_repository()
    if not repo.get_by_id(profile_id):
        return f"error:Profile {profile_id} not found"
    try:
        education = [Education(**e) for e in json.loads(education_json)]
        repo.update(profile_id, ProfileUpdate(education=education))
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


@function_tool
def update_profile_keywords(profile_id: int, keywords: list[str]) -> str:
    repo = _get_profile_repository()
    if not repo.get_by_id(profile_id):
        return f"error:Profile {profile_id} not found"
    try:
        repo.update(profile_id, ProfileUpdate(keywords=keywords))
        return "success"
    except Exception as e:
        return f"error:{str(e)}"


BUILDER_INSTRUCTIONS = "Build or update a profile from parsed resume data."


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
    from agents import Runner

    result = await Runner.run(
        profile_builder_agent,
        f"Build a profile from this parsed resume data: {parsed_resume.model_dump_json()}",
    )
    return result.final_output_as(ProfileBuildResult)


class JobSearchResult(BaseModel):
    total_found: int = Field(description="Total jobs found")
    jobs: list[dict] = Field(default_factory=list, description="Jobs")
    boards_searched: list[str] = Field(default_factory=list, description="Boards searched")
    errors: list[str] = Field(default_factory=list, description="Errors")


def _search_board_sync(client_class, keywords: list[str]) -> tuple[list[dict], Optional[str]]:
    try:
        with client_class() as client:
            jobs = client.search(keywords)
            return [job.model_dump() for job in jobs], None
    except Exception as e:
        return [], str(e)


@function_tool
def search_remoteok(keywords: list[str]) -> str:
    import json

    jobs, error = _search_board_sync(RemoteOKClient, keywords)
    return f"error:{error}" if error else json.dumps({"source": "remoteok", "count": len(jobs), "jobs": jobs})


@function_tool
def search_remotive(keywords: list[str]) -> str:
    import json

    jobs, error = _search_board_sync(RemotiveClient, keywords)
    return f"error:{error}" if error else json.dumps({"source": "remotive", "count": len(jobs), "jobs": jobs})


@function_tool
def search_arbeitnow(keywords: list[str]) -> str:
    import json

    jobs, error = _search_board_sync(ArbeitnowClient, keywords)
    return f"error:{error}" if error else json.dumps({"source": "arbeitnow", "count": len(jobs), "jobs": jobs})


SEARCH_INSTRUCTIONS = "Search remote job boards for matching jobs."


job_search_agent = Agent(
    name="JobSearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[search_remoteok, search_remotive, search_arbeitnow],
    output_type=JobSearchResult,
)


async def search_jobs(keywords: list[str]) -> JobSearchResult:
    from agents import Runner

    result = await Runner.run(
        job_search_agent,
        f"Search for remote jobs matching these keywords: {', '.join(keywords)}",
    )
    return result.final_output_as(JobSearchResult)


async def search_jobs_direct(keywords: list[str]) -> JobSearchResult:
    all_jobs = []
    boards_searched = []
    errors = []
    client_classes = [RemoteOKClient, RemotiveClient, ArbeitnowClient]

    def search_one(client_class):
        with client_class() as client:
            try:
                jobs = client.search(keywords)
                return client.source_name, [j.model_dump() for j in jobs], None
            except Exception as e:
                return client.source_name, [], str(e)

    loop = asyncio.get_event_loop()
    tasks = [loop.run_in_executor(None, search_one, c) for c in client_classes]
    results = await asyncio.gather(*tasks)

    for source, jobs, error in results:
        if error:
            errors.append(f"{source}: {error}")
        else:
            boards_searched.append(source)
            all_jobs.extend(jobs)

    return JobSearchResult(
        total_found=len(all_jobs),
        jobs=all_jobs,
        boards_searched=boards_searched,
        errors=errors,
    )


class MatchedJob(BaseModel):
    job_id: int = Field(description="Database ID")
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    match_score: float = Field(description="Overall score")
    match_explanation: str = Field(description="Explanation")


class MatchingResult(BaseModel):
    total_evaluated: int = Field(description="Total evaluated")
    total_matched: int = Field(description="Matched jobs")
    matched_jobs: list[MatchedJob] = Field(default_factory=list)
    skipped_count: int = Field(default=0)


def _get_repositories():
    session = SessionFactory()
    return ProfileRepository(session), JobRepository(session)


@function_tool
def get_profile_data(profile_id: int) -> str:
    import json

    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        return f"error:Profile {profile_id} not found"
    return json.dumps(
        {
            "id": profile.id,
            "name": profile.name,
            "skills": profile.get_skills(),
            "keywords": profile.get_keywords(),
            "experience": profile.get_experience(),
            "summary": profile.summary,
        }
    )


@function_tool
def calculate_job_match(profile_id: int, job_json: str) -> str:
    import json

    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        return f"error:Profile {profile_id} not found"
    try:
        job_data = json.loads(job_json)
    except json.JSONDecodeError as e:
        return f"error:Invalid job JSON: {e}"
    result = calculate_match_score(
        profile_skills=profile.get_skills(),
        profile_experience=profile.get_experience(),
        profile_keywords=profile.get_keywords(),
        job_title=job_data.get("title", ""),
        job_description=job_data.get("description", ""),
        job_required_skills=job_data.get("required_skills", []),
    )
    return json.dumps(
        {
            "overall_score": result.score,
            "skills_score": result.skills_score,
            "experience_score": result.experience_score,
            "keywords_score": result.keywords_score,
            "requirements_score": result.requirements_score,
            "meets_threshold": result.meets_threshold,
        }
    )


@function_tool
def check_job_exists(external_id: str, source: str, profile_id: int) -> str:
    _, job_repo = _get_repositories()
    return "exists" if job_repo.exists(external_id, source, profile_id) else "not_found"


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
    _, job_repo = _get_repositories()
    if job_repo.exists(external_id, source, profile_id):
        return "error:Job already exists for this profile"
    valid_sources = [s.value for s in JobSource]
    if source.lower() not in valid_sources:
        source = "other"
    try:
        job = job_repo.create(
            JobCreate(
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
                match_details=[{"component": "llm_analysis", "score": match_score, "explanation": match_explanation}],
            )
        )
        return f"saved:id={job.id}"
    except Exception as e:
        return f"error:{str(e)}"


MATCHER_INSTRUCTIONS = "Evaluate jobs against a profile and save matching jobs."


job_matcher_agent = Agent(
    name="JobMatcherAgent",
    instructions=MATCHER_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[get_profile_data, calculate_job_match, check_job_exists, save_matched_job],
    output_type=MatchingResult,
)


async def match_jobs(profile_id: int, jobs: list[dict]) -> MatchingResult:
    from agents import Runner
    import json

    result = await Runner.run(
        job_matcher_agent,
        f"Evaluate these jobs for profile {profile_id} and save matches that meet the threshold:\n{json.dumps(jobs)}",
    )
    return result.final_output_as(MatchingResult)


def match_jobs_fast(profile_id: int, jobs: list[dict], threshold: float = 0.6) -> list[dict]:
    profile_repo, _ = _get_repositories()
    profile = profile_repo.get_by_id(profile_id)
    if not profile:
        return []
    matched = []
    for job in jobs:
        result = calculate_match_score(
            profile_skills=profile.get_skills(),
            profile_experience=profile.get_experience(),
            profile_keywords=profile.get_keywords(),
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


__all__ = [
    "ParsedResume",
    "ProfileBuildResult",
    "JobSearchResult",
    "MatchingResult",
    "resume_parser_agent",
    "parse_resume",
    "profile_builder_agent",
    "build_profile",
    "job_search_agent",
    "search_jobs",
    "search_jobs_direct",
    "job_matcher_agent",
    "match_jobs",
    "match_jobs_fast",
]
