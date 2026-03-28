from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class Experience(BaseModel):
    """A single work experience entry."""
    company: str = Field(description="Company name")
    title: str = Field(description="Job title")
    start_date: str = Field(description="Start date (e.g., 'Jan 2020')")
    end_date: str = Field(default="Present", description="End date or 'Present'")
    bullets: List[str] = Field(default_factory=list, description="Achievement bullet points")
    keywords: List[str] = Field(default_factory=list, description="Extracted skill keywords")


class Education(BaseModel):
    """A single education entry."""
    institution: str = Field(description="School or university name")
    degree: str = Field(description="Degree type (e.g., 'B.S.', 'M.S.', 'Ph.D.')")
    field: str = Field(description="Field of study")
    gpa: Optional[str] = Field(default=None, description="GPA if listed")
    graduation_date: str = Field(description="Graduation date")


class CandidateProfile(BaseModel):
    """Structured representation of a candidate's resume."""
    name: str = Field(description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Current location")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    summary: str = Field(description="Professional summary or objective")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    experiences: List[Experience] = Field(default_factory=list, description="Work experience entries")
    education: List[Education] = Field(default_factory=list, description="Education entries")
    certifications: List[str] = Field(default_factory=list, description="Certifications and licenses")
    total_years_experience: Optional[int] = Field(default=None, description="Estimated total years of experience")


class Platform(str, Enum):
    """Supported job search platforms."""
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    ZIPRECRUITER = "ziprecruiter"


class JobPosting(BaseModel):
    """A single job posting scraped from a platform."""
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    description: str = Field(description="Full job description text")
    requirements: List[str] = Field(default_factory=list, description="Listed requirements")
    url: str = Field(description="Direct URL to the job posting")
    platform: str = Field(description="Source platform (linkedin, indeed, etc.)")
    salary_range: Optional[str] = Field(default=None, description="Salary range if listed")
    posted_date: Optional[str] = Field(default=None, description="When the job was posted")
    job_type: Optional[str] = Field(default=None, description="Full-time, part-time, contract, etc.")
    experience_level: Optional[str] = Field(default=None, description="Entry, mid, senior, etc.")


class Recommendation(str, Enum):
    """Job match recommendation."""
    APPLY = "Apply"
    MAYBE = "Maybe"
    SKIP = "Skip"


class JobMatch(BaseModel):
    """Result of matching a candidate profile against a job posting."""
    job: JobPosting = Field(description="The matched job posting")
    score: float = Field(description="Match score from 0.0 to 1.0")
    matching_skills: List[str] = Field(default_factory=list, description="Skills that match the job")
    missing_skills: List[str] = Field(default_factory=list, description="Required skills the candidate lacks")
    recommendation: str = Field(description="Apply, Maybe, or Skip")
    rationale: str = Field(description="Brief explanation of the match assessment")


class JobMatchList(BaseModel):
    """List of job matches from the research crew."""
    matches: List[JobMatch] = Field(description="Ranked list of job matches")


class TailoredResume(BaseModel):
    """A resume tailored for a specific job posting."""
    candidate_name: str = Field(description="Candidate's name")
    target_company: str = Field(description="Target company name")
    target_title: str = Field(description="Target job title")
    tailored_summary: str = Field(description="Rewritten professional summary")
    tailored_skills: List[str] = Field(description="Reordered/filtered skills for this job")
    tailored_experiences: List[str] = Field(description="Rewritten experience bullets emphasizing relevant achievements")
    output_path: Optional[str] = Field(default=None, description="Path where tailored resume was saved")


class CoverLetter(BaseModel):
    """A cover letter generated for a specific job application."""
    candidate_name: str = Field(description="Candidate's name")
    target_company: str = Field(description="Target company")
    target_title: str = Field(description="Target job title")
    content: str = Field(description="Full cover letter text")
    output_path: Optional[str] = Field(default=None, description="Path where cover letter was saved")


class ApplicationStatus(str, Enum):
    """Status of a job application submission."""
    SUBMITTED = "submitted"
    FAILED = "failed"
    BLOCKED = "blocked"


class ApplicationResult(BaseModel):
    """Result of attempting to submit a job application."""
    job_url: str = Field(description="URL of the job posting")
    job_title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    platform: str = Field(description="Platform where applied")
    status: str = Field(description="submitted, failed, or blocked")
    screenshot_path: Optional[str] = Field(default=None, description="Path to submission screenshot")
    error_message: Optional[str] = Field(default=None, description="Error details if failed/blocked")
    resume_path: Optional[str] = Field(default=None, description="Path to tailored resume used")
    cover_letter_path: Optional[str] = Field(default=None, description="Path to cover letter used")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="When the application was attempted")


class SearchCriteria(BaseModel):
    """User-defined job search parameters."""
    keywords: List[str] = Field(description="Job search keywords (e.g., ['python developer', 'backend engineer'])")
    locations: List[str] = Field(default_factory=lambda: ["Remote"], description="Target locations")
    job_types: List[str] = Field(default_factory=lambda: ["Full-time"], description="Job types to search for")
    experience_level: Optional[str] = Field(default=None, description="Experience level filter")
    salary_min: Optional[int] = Field(default=None, description="Minimum salary filter")
    platforms: List[str] = Field(
        default_factory=lambda: ["linkedin", "indeed", "glassdoor", "ziprecruiter"],
        description="Platforms to search"
    )
    max_results_per_platform: int = Field(default=25, description="Max jobs to scrape per platform")
