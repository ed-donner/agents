"""Tests for database models and repository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.models import Base, Job, Profile, init_database
from src.db.repository import JobRepository, ProfileRepository
from src.schemas.profile import ProfileCreate, ProfileUpdate, Skill, Experience
from src.schemas.job import JobCreate, JobUpdate, MatchDetail


@pytest.fixture
def db_session(tmp_path):
    """Create a temporary database session for testing."""
    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"
    Session = init_database(database_url)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def profile_repo(db_session):
    """Create ProfileRepository instance."""
    return ProfileRepository(db_session)


@pytest.fixture
def job_repo(db_session):
    """Create JobRepository instance."""
    return JobRepository(db_session)


class TestProfileModel:
    """Tests for Profile model."""

    def test_create_profile(self, db_session):
        """Test creating a profile directly."""
        profile = Profile(
            name="Alice Smith",
            email="alice@example.com",
            summary="Backend developer",
        )
        profile.set_skills([{"name": "Python", "level": "expert"}])
        profile.set_keywords(["python", "backend", "api"])

        db_session.add(profile)
        db_session.commit()

        assert profile.id is not None
        assert profile.get_skills() == [{"name": "Python", "level": "expert"}]
        assert profile.get_keywords() == ["python", "backend", "api"]

    def test_profile_json_serialization(self, db_session):
        """Test JSON field serialization and deserialization."""
        profile = Profile(name="Bob", email="bob@example.com")
        profile.set_experience([
            {"company": "Acme", "title": "Developer", "start_date": "2020-01"}
        ])
        profile.set_education([
            {"institution": "MIT", "degree": "BS", "year": 2019}
        ])

        db_session.add(profile)
        db_session.commit()
        db_session.refresh(profile)

        experience = profile.get_experience()
        education = profile.get_education()

        assert len(experience) == 1
        assert experience[0]["company"] == "Acme"
        assert len(education) == 1
        assert education[0]["institution"] == "MIT"


class TestJobModel:
    """Tests for Job model."""

    def test_create_job(self, db_session):
        """Test creating a job with profile relationship."""
        profile = Profile(name="Test User", email="test@example.com")
        db_session.add(profile)
        db_session.commit()

        job = Job(
            profile_id=profile.id,
            external_id="ext-123",
            source="remoteok",
            title="Python Developer",
            company="Tech Corp",
            description="Great opportunity",
            url="https://example.com/job/123",
            match_score=0.95,
        )
        job.set_required_skills(["Python", "Django"])

        db_session.add(job)
        db_session.commit()

        assert job.id is not None
        assert job.profile_id == profile.id
        assert job.get_required_skills() == ["Python", "Django"]

    def test_job_match_details(self, db_session):
        """Test match_details JSON serialization."""
        profile = Profile(name="User", email="user@example.com")
        db_session.add(profile)
        db_session.commit()

        job = Job(
            profile_id=profile.id,
            external_id="ext-456",
            source="remotive",
            title="Backend Engineer",
            company="Startup Inc",
            description="Join us",
            url="https://example.com/job/456",
            match_score=0.92,
        )
        job.set_match_details({
            "skills_score": 0.9,
            "experience_score": 0.85,
            "keywords_score": 0.88,
            "requirements_score": 0.95,
            "matched_skills": ["Python", "AWS"],
        })

        db_session.add(job)
        db_session.commit()

        details = job.get_match_details()
        assert details["skills_score"] == 0.9
        assert "Python" in details["matched_skills"]


class TestProfileRepository:
    """Tests for ProfileRepository."""

    def test_create_profile(self, profile_repo):
        """Test creating a profile through repository."""
        data = ProfileCreate(
            name="Jane Doe",
            email="jane@example.com",
            summary="Full-stack developer",
            skills=[Skill(name="JavaScript", level="advanced", years=5)],
        )
        profile = profile_repo.create(data)

        assert profile.id is not None
        assert profile.name == "Jane Doe"
        assert len(profile.get_skills()) == 1

    def test_get_by_id(self, profile_repo):
        """Test getting profile by ID."""
        data = ProfileCreate(name="John", email="john@example.com")
        created = profile_repo.create(data)

        fetched = profile_repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.email == "john@example.com"

    def test_get_by_email(self, profile_repo):
        """Test getting profile by email."""
        data = ProfileCreate(name="Alice", email="alice@test.com")
        profile_repo.create(data)

        fetched = profile_repo.get_by_email("alice@test.com")
        assert fetched is not None
        assert fetched.name == "Alice"

    def test_update_profile(self, profile_repo):
        """Test updating a profile."""
        data = ProfileCreate(name="Original", email="original@test.com")
        profile = profile_repo.create(data)

        update_data = ProfileUpdate(name="Updated", summary="New summary")
        updated = profile_repo.update(profile.id, update_data)

        assert updated.name == "Updated"
        assert updated.summary == "New summary"
        assert updated.email == "original@test.com"

    def test_delete_profile(self, profile_repo):
        """Test deleting a profile."""
        data = ProfileCreate(name="ToDelete", email="delete@test.com")
        profile = profile_repo.create(data)
        profile_id = profile.id

        result = profile_repo.delete(profile_id)
        assert result is True

        fetched = profile_repo.get_by_id(profile_id)
        assert fetched is None


class TestJobRepository:
    """Tests for JobRepository."""

    @pytest.fixture
    def test_profile(self, profile_repo):
        """Create a test profile for job tests."""
        data = ProfileCreate(name="Test", email="test@jobs.com")
        return profile_repo.create(data)

    def test_create_job(self, job_repo, test_profile):
        """Test creating a job through repository."""
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="job-001",
            source="remoteok",
            title="Senior Developer",
            company="Tech Co",
            description="Great role",
            required_skills=["Python", "AWS"],
            url="https://example.com/job/001",
            match_score=0.93,
        )
        job = job_repo.create(data)

        assert job.id is not None
        assert job.title == "Senior Developer"
        assert job.status == "new"

    def test_get_by_profile(self, job_repo, test_profile):
        """Test getting jobs by profile."""
        for i in range(5):
            data = JobCreate(
                profile_id=test_profile.id,
                external_id=f"job-{i}",
                source="remotive",
                title=f"Job {i}",
                company="Company",
                description="Description",
                url=f"https://example.com/job/{i}",
                match_score=0.9 + (i * 0.01),
            )
            job_repo.create(data)

        jobs = job_repo.get_by_profile(test_profile.id)
        assert len(jobs) == 5
        assert jobs[0].match_score >= jobs[-1].match_score

    def test_filter_by_status(self, job_repo, test_profile):
        """Test filtering jobs by status."""
        data1 = JobCreate(
            profile_id=test_profile.id,
            external_id="job-new",
            source="remoteok",
            title="New Job",
            company="Co",
            description="Desc",
            url="https://example.com/1",
            match_score=0.91,
        )
        data2 = JobCreate(
            profile_id=test_profile.id,
            external_id="job-applied",
            source="remoteok",
            title="Applied Job",
            company="Co",
            description="Desc",
            url="https://example.com/2",
            match_score=0.92,
        )
        job_repo.create(data1)
        job2 = job_repo.create(data2)
        job_repo.update(job2.id, JobUpdate(status="applied"))

        new_jobs = job_repo.get_by_profile(test_profile.id, status="new")
        applied_jobs = job_repo.get_by_profile(test_profile.id, status="applied")

        assert len(new_jobs) == 1
        assert len(applied_jobs) == 1

    def test_update_job_status(self, job_repo, test_profile):
        """Test updating job status."""
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="status-test",
            source="arbeitnow",
            title="Status Test",
            company="Co",
            description="Desc",
            url="https://example.com/status",
            match_score=0.90,
        )
        job = job_repo.create(data)

        updated = job_repo.update(job.id, JobUpdate(status="interview", notes="Phone screen"))

        assert updated.status == "interview"
        assert updated.notes == "Phone screen"

    def test_job_exists(self, job_repo, test_profile):
        """Test checking if job exists."""
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="exists-test",
            source="remoteok",
            title="Exists Test",
            company="Co",
            description="Desc",
            url="https://example.com/exists",
            match_score=0.91,
        )
        job_repo.create(data)

        assert job_repo.exists("exists-test", "remoteok", test_profile.id) is True
        assert job_repo.exists("nonexistent", "remoteok", test_profile.id) is False

    def test_get_stats(self, job_repo, test_profile):
        """Test getting job statistics."""
        statuses = ["new", "new", "applied", "interview", "rejected"]
        for i, status in enumerate(statuses):
            data = JobCreate(
                profile_id=test_profile.id,
                external_id=f"stats-{i}",
                source="remotive",
                title=f"Stats Job {i}",
                company="Co",
                description="Desc",
                url=f"https://example.com/stats/{i}",
                match_score=0.90 + (i * 0.01),
            )
            job = job_repo.create(data)
            if status != "new":
                job_repo.update(job.id, JobUpdate(status=status))

        stats = job_repo.get_stats(test_profile.id)

        assert stats.total_jobs == 5
        assert stats.new_jobs == 2
        assert stats.applied_jobs == 1
        assert stats.interview_jobs == 1
        assert stats.rejected_jobs == 1
        assert stats.avg_match_score > 0.9
