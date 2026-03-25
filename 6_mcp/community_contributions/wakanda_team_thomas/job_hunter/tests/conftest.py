"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory) -> Path:
    """Create a temporary database path for testing."""
    return tmp_path_factory.mktemp("data") / "test_job_hunter.db"


@pytest.fixture
def test_settings(test_db_path, monkeypatch):
    """Create test settings with temporary database."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("DEBUG", "true")

    from src.config import Settings
    return Settings()


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume text for testing."""
    return """
    John Doe
    Senior Software Engineer
    john.doe@email.com | (555) 123-4567

    SUMMARY
    Experienced software engineer with 8+ years in Python, JavaScript, and cloud technologies.
    Specialized in building scalable microservices and data pipelines.

    SKILLS
    - Languages: Python, JavaScript, TypeScript, Go
    - Frameworks: FastAPI, Django, React, Node.js
    - Cloud: AWS, GCP, Docker, Kubernetes
    - Databases: PostgreSQL, MongoDB, Redis
    - Tools: Git, CI/CD, Terraform

    EXPERIENCE
    Senior Software Engineer | Tech Corp | 2020 - Present
    - Led development of microservices architecture serving 10M+ users
    - Implemented CI/CD pipelines reducing deployment time by 70%
    - Mentored team of 5 junior developers

    Software Engineer | StartupXYZ | 2016 - 2020
    - Built real-time data processing pipeline handling 1M events/day
    - Developed RESTful APIs using Python and FastAPI

    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology | 2016
    """


@pytest.fixture
def sample_job_listing() -> dict:
    """Sample job listing for testing."""
    return {
        "external_id": "job-123",
        "source": "remoteok",
        "title": "Senior Python Developer",
        "company": "Remote Tech Inc",
        "description": """
        We're looking for a Senior Python Developer to join our team.
        
        Requirements:
        - 5+ years of Python experience
        - Experience with FastAPI or Django
        - Strong knowledge of AWS or GCP
        - Experience with PostgreSQL
        - Excellent communication skills
        
        Nice to have:
        - Kubernetes experience
        - Go programming experience
        """,
        "required_skills": ["Python", "FastAPI", "AWS", "PostgreSQL"],
        "salary_range": "$120k - $160k",
        "url": "https://example.com/job/123",
        "posted_at": "2026-03-20T10:00:00Z",
    }
