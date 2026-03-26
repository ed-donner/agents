"""Pydantic schemas for user profile data."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


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
