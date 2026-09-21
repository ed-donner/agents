"""Pydantic schemas for profile and job data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.config import JobSource, JobStatus


class Skill(BaseModel):
    """Individual skill with optional proficiency level."""

    name: str = Field(..., description="Skill name")
    level: Optional[str] = Field(
        default=None, description="Proficiency level (beginner/intermediate/advanced/expert)"
    )
    years: Optional[float] = Field(default=None, ge=0, description="Years of experience")


class Experience(BaseModel):
    """Work experience entry."""

    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    start_date: Optional[str] = Field(default=None, description="Start date")
    end_date: Optional[str] = Field(default=None, description="End date or 'Present'")
    description: Optional[str] = Field(default=None, description="Role description")
    location: Optional[str] = Field(default=None, description="Job location")


class Education(BaseModel):
    """Education entry."""

    institution: str = Field(..., description="School/University name")
    degree: Optional[str] = Field(default=None, description="Degree obtained")
    field: Optional[str] = Field(default=None, description="Field of study")
    graduation_date: Optional[str] = Field(default=None, description="Graduation date")


class JobPreferences(BaseModel):
    """User's job search preferences."""

    desired_titles: list[str] = Field(
        default_factory=list, description="Preferred job titles"
    )
    min_salary: Optional[int] = Field(default=None, description="Minimum salary expectation")
    preferred_industries: list[str] = Field(
        default_factory=list, description="Preferred industries"
    )
    excluded_companies: list[str] = Field(
        default_factory=list, description="Companies to exclude"
    )


class ProfileCreate(BaseModel):
    """Schema for creating a new profile."""

    name: str = Field(..., min_length=1, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    summary: Optional[str] = Field(default=None, description="Professional summary")
    skills: list[Skill] = Field(default_factory=list, description="List of skills")
    experience: list[Experience] = Field(
        default_factory=list, description="Work experience"
    )
    education: list[Education] = Field(
        default_factory=list, description="Education history"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Keywords extracted from resume"
    )
    preferences: Optional[JobPreferences] = Field(
        default=None, description="Job search preferences"
    )
    resume_path: Optional[str] = Field(
        default=None, description="Path to uploaded resume"
    )
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Current location")


class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile."""

    name: Optional[str] = Field(default=None, min_length=1, description="Full name")
    email: Optional[EmailStr] = Field(default=None, description="Email address")
    summary: Optional[str] = Field(default=None, description="Professional summary")
    skills: Optional[list[Skill]] = Field(default=None, description="List of skills")
    experience: Optional[list[Experience]] = Field(
        default=None, description="Work experience"
    )
    education: Optional[list[Education]] = Field(
        default=None, description="Education history"
    )
    keywords: Optional[list[str]] = Field(
        default=None, description="Keywords extracted from resume"
    )
    preferences: Optional[JobPreferences] = Field(
        default=None, description="Job search preferences"
    )
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Current location")


class ProfileResponse(BaseModel):
    """Schema for profile response."""

    id: int = Field(..., description="Profile ID")
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    summary: Optional[str] = Field(default=None, description="Professional summary")
    skills: list[Skill] = Field(default_factory=list, description="List of skills")
    experience: list[Experience] = Field(
        default_factory=list, description="Work experience"
    )
    education: list[Education] = Field(
        default_factory=list, description="Education history"
    )
    keywords: list[str] = Field(
        default_factory=list, description="Keywords extracted from resume"
    )
    preferences: Optional[JobPreferences] = Field(
        default=None, description="Job search preferences"
    )
    resume_path: Optional[str] = Field(
        default=None, description="Path to uploaded resume"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class MatchDetail(BaseModel):
    """Detailed breakdown of job-profile match."""

    skills_score: float = Field(..., ge=0, le=1, description="Skills match score")
    experience_score: float = Field(..., ge=0, le=1, description="Experience match score")
    keywords_score: float = Field(..., ge=0, le=1, description="Keywords overlap score")
    requirements_score: float = Field(
        ..., ge=0, le=1, description="Requirements match score"
    )
    matched_skills: list[str] = Field(
        default_factory=list, description="Skills that matched"
    )
    missing_skills: list[str] = Field(
        default_factory=list, description="Required skills not in profile"
    )
    explanation: Optional[str] = Field(
        default=None, description="LLM-generated match explanation"
    )


class JobCreate(BaseModel):
    """Schema for creating a new job entry."""

    profile_id: int = Field(..., description="Associated profile ID")
    external_id: str = Field(..., description="Job ID from source board")
    source: str = Field(..., description="Job board source")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    location: Optional[str] = Field(default=None, description="Job location")
    required_skills: list[str] = Field(
        default_factory=list, description="Required skills"
    )
    salary_range: Optional[str] = Field(default=None, description="Salary range")
    url: str = Field(..., description="Job posting URL")
    match_score: float = Field(..., ge=0, le=1, description="Overall match score")
    match_details: Optional[list] = Field(default=None, description="Match details")
    posted_at: Optional[datetime] = Field(
        default=None, description="When job was posted"
    )

    def model_post_init(self, *args, **kwargs):
        if self.source not in JobSource.ALL:
            pass


class JobUpdate(BaseModel):
    """Schema for updating job status and notes."""

    status: Optional[str] = Field(default=None, description="Application status")
    notes: Optional[str] = Field(default=None, description="User notes")

    def model_post_init(self, *args, **kwargs):
        if self.status is not None and self.status not in JobStatus.ALL:
            raise ValueError(f"Invalid status. Must be one of: {JobStatus.ALL}")


class JobResponse(BaseModel):
    """Schema for job response."""

    id: int = Field(..., description="Job ID")
    profile_id: int = Field(..., description="Associated profile ID")
    external_id: str = Field(..., description="Job ID from source board")
    source: str = Field(..., description="Job board source")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    required_skills: list[str] = Field(
        default_factory=list, description="Required skills"
    )
    salary_range: Optional[str] = Field(default=None, description="Salary range")
    url: str = Field(..., description="Job posting URL")
    match_score: float = Field(..., ge=0, le=1, description="Overall match score")
    match_details: Optional[MatchDetail] = Field(
        default=None, description="Detailed match breakdown"
    )
    status: str = Field(default=JobStatus.NEW, description="Application status")
    notes: Optional[str] = Field(default=None, description="User notes")
    posted_at: Optional[datetime] = Field(
        default=None, description="When job was posted"
    )
    found_at: datetime = Field(..., description="When job was found")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Schema for listing multiple jobs."""

    jobs: list[JobResponse] = Field(default_factory=list, description="List of jobs")
    total: int = Field(..., description="Total number of jobs")
    page: int = Field(default=1, ge=1, description="Current page")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class JobStats(BaseModel):
    """Statistics about jobs for a profile."""

    total_jobs: int = Field(default=0, description="Total jobs found")
    new_jobs: int = Field(default=0, description="Jobs with 'new' status")
    reviewing_jobs: int = Field(default=0, description="Jobs being reviewed")
    applied_jobs: int = Field(default=0, description="Jobs applied to")
    interview_jobs: int = Field(default=0, description="Jobs with interviews")
    rejected_jobs: int = Field(default=0, description="Rejected applications")
    accepted_jobs: int = Field(default=0, description="Accepted offers")
    avg_match_score: float = Field(default=0.0, description="Average match score")


class JobBoardListing(BaseModel):
    """Raw job listing from a job board API."""

    external_id: str = Field(..., description="Job ID from source")
    source: str = Field(..., description="Job board name")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    description: str = Field(..., description="Job description")
    required_skills: list[str] = Field(
        default_factory=list, description="Extracted skills"
    )
    salary_range: Optional[str] = Field(default=None, description="Salary range")
    url: str = Field(..., description="Job posting URL")
    posted_at: Optional[datetime] = Field(
        default=None, description="Posting date"
    )
    location: str = Field(default="Remote", description="Job location")
    is_remote: bool = Field(default=True, description="Is fully remote")
