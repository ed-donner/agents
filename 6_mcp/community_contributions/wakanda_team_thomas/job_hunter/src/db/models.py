"""SQLAlchemy models for the job hunter database."""

import json
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class HuntingBase(DeclarativeBase):
    """Base class for all models."""
    pass


class Profile(HuntingBase):
    """User profile with resume data and job preferences."""

    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    preferences = Column(Text, nullable=True)
    resume_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    jobs = relationship("Job", back_populates="profile", cascade="all, delete-orphan")

    def get_skills(self) -> list[dict]:
        """Deserialize skills JSON."""
        if self.skills:
            return json.loads(self.skills)
        return []

    def set_skills(self, value: list[dict]) -> None:
        """Serialize skills to JSON."""
        self.skills = json.dumps(value) if value else None

    def get_experience(self) -> list[dict]:
        """Deserialize experience JSON."""
        if self.experience:
            return json.loads(self.experience)
        return []

    def set_experience(self, value: list[dict]) -> None:
        """Serialize experience to JSON."""
        self.experience = json.dumps(value) if value else None

    def get_education(self) -> list[dict]:
        """Deserialize education JSON."""
        if self.education:
            return json.loads(self.education)
        return []

    def set_education(self, value: list[dict]) -> None:
        """Serialize education to JSON."""
        self.education = json.dumps(value) if value else None

    def get_keywords(self) -> list[str]:
        """Deserialize keywords JSON."""
        if self.keywords:
            return json.loads(self.keywords)
        return []

    def set_keywords(self, value: list[str]) -> None:
        """Serialize keywords to JSON."""
        self.keywords = json.dumps(value) if value else None

    def get_preferences(self) -> dict | None:
        """Deserialize preferences JSON."""
        if self.preferences:
            return json.loads(self.preferences)
        return None

    def set_preferences(self, value: dict | None) -> None:
        """Serialize preferences to JSON."""
        self.preferences = json.dumps(value) if value else None


class Job(HuntingBase):
    """Job listing matched to a user profile."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    external_id = Column(String(255), nullable=False)
    source = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    required_skills = Column(Text, nullable=True)
    salary_range = Column(String(100), nullable=True)
    url = Column(String(1024), nullable=False)
    match_score = Column(Float, nullable=False)
    match_details = Column(Text, nullable=True)
    status = Column(String(50), default="new")
    notes = Column(Text, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    found_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    profile = relationship("Profile", back_populates="jobs")

    def get_required_skills(self) -> list[str]:
        """Deserialize required_skills JSON."""
        if self.required_skills:
            return json.loads(self.required_skills)
        return []

    def set_required_skills(self, value: list[str]) -> None:
        """Serialize required_skills to JSON."""
        self.required_skills = json.dumps(value) if value else None

    def get_match_details(self) -> dict | None:
        """Deserialize match_details JSON."""
        if self.match_details:
            return json.loads(self.match_details)
        return None

    def set_match_details(self, value: dict | None) -> None:
        """Serialize match_details to JSON."""
        self.match_details = json.dumps(value) if value else None


def init_database(database_url: str) -> sessionmaker:
    """Initialize database and return session factory."""
    engine = create_engine(database_url, echo=False)
    HuntingBase.metadata.create_all(engine)
    return sessionmaker(bind=engine)
