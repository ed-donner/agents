"""Tests for Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas import (
    Skill,
    Experience,
    Education,
    JobPreferences,
    ProfileCreate,
    ProfileUpdate,
    MatchDetail,
    JobCreate,
    JobUpdate,
    JobResponse,
    JobStats,
    JobBoardListing,
)


class TestProfileSchemas:
    """Test profile-related schemas."""

    def test_skill_creation(self):
        """Test Skill schema."""
        skill = Skill(name="Python", level="expert", years=5.0)
        assert skill.name == "Python"
        assert skill.level == "expert"
        assert skill.years == 5.0

    def test_skill_minimal(self):
        """Test Skill with only required field."""
        skill = Skill(name="JavaScript")
        assert skill.name == "JavaScript"
        assert skill.level is None
        assert skill.years is None

    def test_experience_creation(self):
        """Test Experience schema."""
        exp = Experience(
            company="Tech Corp",
            title="Senior Developer",
            start_date="2020-01",
            end_date="Present",
            achievements=["Led team of 5", "Shipped v2.0"],
        )
        assert exp.company == "Tech Corp"
        assert len(exp.achievements) == 2

    def test_education_creation(self):
        """Test Education schema."""
        edu = Education(
            institution="MIT",
            degree="Bachelor of Science",
            field="Computer Science",
            year=2016,
        )
        assert edu.institution == "MIT"
        assert edu.year == 2016

    def test_profile_create_valid(self):
        """Test valid ProfileCreate."""
        profile = ProfileCreate(
            name="John Doe",
            email="john@example.com",
            summary="Experienced developer",
            skills=[Skill(name="Python")],
        )
        assert profile.name == "John Doe"
        assert profile.email == "john@example.com"

    def test_profile_create_invalid_email(self):
        """Test ProfileCreate with invalid email."""
        with pytest.raises(ValidationError):
            ProfileCreate(name="John Doe", email="invalid-email")

    def test_profile_create_empty_name(self):
        """Test ProfileCreate with empty name."""
        with pytest.raises(ValidationError):
            ProfileCreate(name="", email="john@example.com")

    def test_profile_update_partial(self):
        """Test ProfileUpdate with partial data."""
        update = ProfileUpdate(name="Jane Doe")
        assert update.name == "Jane Doe"
        assert update.email is None
        assert update.skills is None


class TestJobSchemas:
    """Test job-related schemas."""

    def test_match_detail_creation(self):
        """Test MatchDetail schema."""
        match = MatchDetail(
            skills_score=0.85,
            experience_score=0.90,
            keywords_score=0.75,
            requirements_score=0.80,
            matched_skills=["Python", "AWS"],
            missing_skills=["Kubernetes"],
        )
        assert match.skills_score == 0.85
        assert "Python" in match.matched_skills

    def test_match_detail_invalid_score(self):
        """Test MatchDetail with invalid score."""
        with pytest.raises(ValidationError):
            MatchDetail(
                skills_score=1.5,  # Invalid: > 1.0
                experience_score=0.90,
                keywords_score=0.75,
                requirements_score=0.80,
            )

    def test_job_create_valid(self):
        """Test valid JobCreate."""
        job = JobCreate(
            profile_id=1,
            external_id="job-123",
            source="remoteok",
            title="Python Developer",
            company="Remote Inc",
            description="Great opportunity...",
            required_skills=["Python", "FastAPI"],
            url="https://example.com/job",
            match_score=0.92,
        )
        assert job.title == "Python Developer"
        assert job.match_score == 0.92

    def test_job_update_valid_status(self):
        """Test JobUpdate with valid status."""
        update = JobUpdate(status="applied", notes="Submitted application")
        assert update.status == "applied"

    def test_job_update_invalid_status(self):
        """Test JobUpdate with invalid status."""
        with pytest.raises(ValidationError):
            JobUpdate(status="invalid_status")

    def test_job_stats_defaults(self):
        """Test JobStats default values."""
        stats = JobStats()
        assert stats.total_jobs == 0
        assert stats.avg_match_score == 0.0

    def test_job_board_listing(self):
        """Test JobBoardListing schema."""
        listing = JobBoardListing(
            external_id="abc123",
            source="remotive",
            title="Backend Developer",
            company="Startup XYZ",
            description="Join our team...",
            url="https://remotive.com/job/abc123",
            is_remote=True,
        )
        assert listing.is_remote is True
        assert listing.location == "Remote"
