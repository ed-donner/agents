"""Pydantic schemas for job data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

from src.config import JobStatus, JobSource


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
    match_details: Optional[list] = Field(
        default=None, description="Match details"
    )
    posted_at: Optional[datetime] = Field(
        default=None, description="When job was posted"
    )

    def model_post_init(self, *args, **kwargs):
        """Validate source is a known job board."""
        if self.source not in JobSource.ALL:
            pass  # Allow unknown sources for flexibility


class JobUpdate(BaseModel):
    """Schema for updating job status and notes."""

    status: Optional[str] = Field(default=None, description="Application status")
    notes: Optional[str] = Field(default=None, description="User notes")

    def model_post_init(self, *args, **kwargs):
        """Validate status is valid."""
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
