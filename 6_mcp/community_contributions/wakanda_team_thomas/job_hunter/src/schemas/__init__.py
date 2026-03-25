"""Pydantic schemas for data validation."""

from src.schemas.profile import (
    Skill,
    Experience,
    Education,
    JobPreferences,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
)
from src.schemas.job import (
    MatchDetail,
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobStats,
    JobBoardListing,
)

__all__ = [
    "Skill",
    "Experience",
    "Education",
    "JobPreferences",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "MatchDetail",
    "JobCreate",
    "JobUpdate",
    "JobResponse",
    "JobListResponse",
    "JobStats",
    "JobBoardListing",
]
