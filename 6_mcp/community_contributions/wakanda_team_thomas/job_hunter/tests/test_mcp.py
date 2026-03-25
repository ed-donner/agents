"""Integration tests for MCP server tools."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.db.models import init_database
from src.db.repository import ProfileRepository, JobRepository
from src.schemas.profile import ProfileCreate, ProfileUpdate, Skill, Experience
from src.schemas.job import JobCreate, JobUpdate


@pytest.fixture
def db_session(tmp_path):
    """Create a temporary database session for MCP testing."""
    db_path = tmp_path / "test_mcp.db"
    db_url = f"sqlite:///{db_path}"
    Session = init_database(db_url)
    session = Session()
    yield session
    session.close()


class TestMCPProfileWorkflow:
    """Test profile workflow as MCP tools would use it."""

    def test_create_profile_workflow(self, db_session):
        """Test complete profile creation workflow."""
        repo = ProfileRepository(db_session)
        
        data = ProfileCreate(
            name="MCP Test User",
            email="mcp@example.com",
            summary="Test user for MCP",
        )
        profile = repo.create(data)
        
        assert profile.id is not None
        assert profile.name == "MCP Test User"
        
        fetched = repo.get_by_id(profile.id)
        assert fetched.email == "mcp@example.com"

    def test_update_profile_skills_workflow(self, db_session):
        """Test profile skills update workflow."""
        repo = ProfileRepository(db_session)
        
        data = ProfileCreate(name="Skills User", email="skills@example.com")
        profile = repo.create(data)
        
        skills = [Skill(name="Python", level="expert", years=5)]
        update_data = ProfileUpdate(skills=skills)
        updated = repo.update(profile.id, update_data)
        
        assert len(updated.get_skills()) == 1
        assert updated.get_skills()[0]["name"] == "Python"

    def test_update_profile_experience_workflow(self, db_session):
        """Test profile experience update workflow."""
        repo = ProfileRepository(db_session)
        
        data = ProfileCreate(name="Exp User", email="exp@example.com")
        profile = repo.create(data)
        
        experience = [Experience(company="Tech Corp", title="Senior Dev")]
        update_data = ProfileUpdate(experience=experience)
        updated = repo.update(profile.id, update_data)
        
        assert len(updated.get_experience()) == 1

    def test_update_profile_keywords_workflow(self, db_session):
        """Test profile keywords update workflow."""
        repo = ProfileRepository(db_session)
        
        data = ProfileCreate(name="Keywords User", email="keywords@example.com")
        profile = repo.create(data)
        
        update_data = ProfileUpdate(keywords=["python", "aws", "backend"])
        updated = repo.update(profile.id, update_data)
        
        assert "python" in updated.get_keywords()

    def test_list_profiles_workflow(self, db_session):
        """Test listing profiles workflow."""
        repo = ProfileRepository(db_session)
        
        for i in range(3):
            data = ProfileCreate(name=f"User {i}", email=f"user{i}@example.com")
            repo.create(data)
        
        profiles = repo.get_all()
        assert len(profiles) == 3

    def test_delete_profile_workflow(self, db_session):
        """Test profile deletion workflow."""
        repo = ProfileRepository(db_session)
        
        data = ProfileCreate(name="To Delete", email="delete@example.com")
        profile = repo.create(data)
        profile_id = profile.id
        
        result = repo.delete(profile_id)
        assert result is True
        
        fetched = repo.get_by_id(profile_id)
        assert fetched is None


class TestMCPJobWorkflow:
    """Test job workflow as MCP tools would use it."""

    @pytest.fixture
    def test_profile(self, db_session):
        """Create a test profile for job tests."""
        repo = ProfileRepository(db_session)
        data = ProfileCreate(name="Job Test User", email="jobtest@example.com")
        return repo.create(data)

    def test_add_job_workflow(self, db_session, test_profile):
        """Test adding a job workflow."""
        job_repo = JobRepository(db_session)
        
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="mcp-job-1",
            source="remoteok",
            title="Python Developer",
            company="Tech Corp",
            description="Great opportunity",
            url="https://example.com/job/1",
            match_score=0.92,
            required_skills=["Python", "Django"],
        )
        job = job_repo.create(data)
        
        assert job.id is not None
        assert job.title == "Python Developer"
        assert job.status == "new"

    def test_list_jobs_workflow(self, db_session, test_profile):
        """Test listing jobs workflow."""
        job_repo = JobRepository(db_session)
        
        for i in range(5):
            data = JobCreate(
                profile_id=test_profile.id,
                external_id=f"list-job-{i}",
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

    def test_filter_jobs_by_status_workflow(self, db_session, test_profile):
        """Test filtering jobs by status workflow."""
        job_repo = JobRepository(db_session)
        
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="filter-job",
            source="arbeitnow",
            title="Filter Job",
            company="Co",
            description="Desc",
            url="https://example.com/filter",
            match_score=0.91,
        )
        job = job_repo.create(data)
        
        job_repo.update(job.id, JobUpdate(status="applied"))
        
        new_jobs = job_repo.get_by_profile(test_profile.id, status="new")
        applied_jobs = job_repo.get_by_profile(test_profile.id, status="applied")
        
        assert len(applied_jobs) == 1
        assert applied_jobs[0].status == "applied"

    def test_update_job_status_workflow(self, db_session, test_profile):
        """Test updating job status workflow."""
        job_repo = JobRepository(db_session)
        
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="status-job",
            source="remoteok",
            title="Status Job",
            company="Co",
            description="Desc",
            url="https://example.com/status",
            match_score=0.93,
        )
        job = job_repo.create(data)
        
        update_data = JobUpdate(status="interview", notes="Phone screen scheduled")
        updated = job_repo.update(job.id, update_data)
        
        assert updated.status == "interview"
        assert updated.notes == "Phone screen scheduled"

    def test_delete_job_workflow(self, db_session, test_profile):
        """Test deleting a job workflow."""
        job_repo = JobRepository(db_session)
        
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="delete-job",
            source="remotive",
            title="To Delete",
            company="Co",
            description="Desc",
            url="https://example.com/delete",
            match_score=0.9,
        )
        job = job_repo.create(data)
        job_id = job.id
        
        result = job_repo.delete(job_id)
        assert result is True
        
        fetched = job_repo.get_by_id(job_id)
        assert fetched is None

    def test_job_stats_workflow(self, db_session, test_profile):
        """Test getting job statistics workflow."""
        job_repo = JobRepository(db_session)
        
        statuses = ["new", "new", "applied", "interview"]
        for i, status in enumerate(statuses):
            data = JobCreate(
                profile_id=test_profile.id,
                external_id=f"stats-{i}",
                source="remoteok",
                title=f"Stats Job {i}",
                company="Co",
                description="Desc",
                url=f"https://example.com/stats/{i}",
                match_score=0.90 + (i * 0.02),
            )
            job = job_repo.create(data)
            if status != "new":
                job_repo.update(job.id, JobUpdate(status=status))
        
        stats = job_repo.get_stats(test_profile.id)
        
        assert stats.total_jobs == 4
        assert stats.new_jobs == 2
        assert stats.applied_jobs == 1
        assert stats.interview_jobs == 1
        assert stats.avg_match_score > 0.9

    def test_check_job_exists_workflow(self, db_session, test_profile):
        """Test checking if job exists workflow."""
        job_repo = JobRepository(db_session)
        
        data = JobCreate(
            profile_id=test_profile.id,
            external_id="exists-check",
            source="remoteok",
            title="Exists Job",
            company="Co",
            description="Desc",
            url="https://example.com/exists",
            match_score=0.91,
        )
        job_repo.create(data)
        
        assert job_repo.exists("exists-check", "remoteok", test_profile.id) is True
        assert job_repo.exists("nonexistent", "remoteok", test_profile.id) is False


class TestMCPServerLoad:
    """Test that MCP server loads correctly."""

    def test_mcp_server_imports(self):
        """Test MCP server can be imported."""
        from src.mcp_server.server import mcp
        assert mcp is not None

    def test_mcp_server_has_tools(self):
        """Test MCP server has all expected tools."""
        from src.mcp_server.server import mcp
        
        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        
        expected_profile_tools = [
            "create_profile",
            "get_profile",
            "update_profile_skills",
            "update_profile_experience",
            "update_profile_education",
            "update_profile_keywords",
            "list_profiles",
            "delete_profile",
        ]
        
        expected_job_tools = [
            "add_job",
            "get_job",
            "list_jobs",
            "update_job_status",
            "delete_job",
            "get_job_stats",
        ]
        
        for tool in expected_profile_tools:
            assert tool in tool_names, f"Missing profile tool: {tool}"
        
        for tool in expected_job_tools:
            assert tool in tool_names, f"Missing job tool: {tool}"

    def test_mcp_server_tool_count(self):
        """Test MCP server has correct number of tools."""
        from src.mcp_server.server import mcp
        
        tool_count = len(mcp._tool_manager._tools)
        assert tool_count == 14
