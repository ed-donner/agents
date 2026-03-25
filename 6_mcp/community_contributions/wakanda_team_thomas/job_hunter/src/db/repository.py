"""Repository pattern for database operations."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.db.models import Job, Profile
from src.schemas.job import JobCreate, JobStats, JobUpdate
from src.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileRepository:
    """Data access layer for profiles."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: ProfileCreate) -> Profile:
        """Create a new profile."""
        profile = Profile(
            name=data.name,
            email=data.email,
            summary=data.summary,
            resume_path=data.resume_path,
        )
        profile.set_skills([s.model_dump() for s in data.skills])
        profile.set_experience([e.model_dump() for e in data.experience])
        profile.set_education([e.model_dump() for e in data.education])
        profile.set_keywords(data.keywords)
        if data.preferences:
            profile.set_preferences(data.preferences.model_dump())

        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def get_by_id(self, profile_id: int) -> Optional[Profile]:
        """Get profile by ID."""
        return self.session.query(Profile).filter(Profile.id == profile_id).first()

    def get_by_email(self, email: str) -> Optional[Profile]:
        """Get profile by email."""
        return self.session.query(Profile).filter(Profile.email == email).first()

    def get_all(self) -> list[Profile]:
        """Get all profiles."""
        return self.session.query(Profile).all()

    def update(self, profile_id: int, data: ProfileUpdate) -> Optional[Profile]:
        """Update an existing profile."""
        profile = self.get_by_id(profile_id)
        if not profile:
            return None

        if data.name is not None:
            profile.name = data.name
        if data.email is not None:
            profile.email = data.email
        if data.summary is not None:
            profile.summary = data.summary
        if data.skills is not None:
            profile.set_skills([s.model_dump() for s in data.skills])
        if data.experience is not None:
            profile.set_experience([e.model_dump() for e in data.experience])
        if data.education is not None:
            profile.set_education([e.model_dump() for e in data.education])
        if data.keywords is not None:
            profile.set_keywords(data.keywords)
        if data.preferences is not None:
            profile.set_preferences(data.preferences.model_dump())

        profile.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(profile)
        return profile

    def delete(self, profile_id: int) -> bool:
        """Delete a profile."""
        profile = self.get_by_id(profile_id)
        if not profile:
            return False

        self.session.delete(profile)
        self.session.commit()
        return True


class JobRepository:
    """Data access layer for jobs."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, data: JobCreate) -> Job:
        """Create a new job entry."""
        job = Job(
            profile_id=data.profile_id,
            external_id=data.external_id,
            source=data.source,
            title=data.title,
            company=data.company,
            description=data.description,
            salary_range=data.salary_range,
            url=data.url,
            match_score=data.match_score,
            posted_at=data.posted_at,
        )
        job.set_required_skills(data.required_skills)
        if data.match_details:
            job.set_match_details(data.match_details.model_dump())

        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> Optional[Job]:
        """Get job by ID."""
        return self.session.query(Job).filter(Job.id == job_id).first()

    def get_by_external_id(self, external_id: str, source: str) -> Optional[Job]:
        """Get job by external ID and source."""
        return (
            self.session.query(Job)
            .filter(Job.external_id == external_id, Job.source == source)
            .first()
        )

    def get_by_profile(
        self,
        profile_id: int,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get jobs for a profile with optional filters."""
        query = self.session.query(Job).filter(Job.profile_id == profile_id)

        if status:
            query = query.filter(Job.status == status)
        if min_score is not None:
            query = query.filter(Job.match_score >= min_score)

        query = query.order_by(Job.match_score.desc(), Job.found_at.desc())
        return query.offset(offset).limit(limit).all()

    def count_by_profile(
        self,
        profile_id: int,
        status: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> int:
        """Count jobs for a profile with optional filters."""
        query = self.session.query(Job).filter(Job.profile_id == profile_id)

        if status:
            query = query.filter(Job.status == status)
        if min_score is not None:
            query = query.filter(Job.match_score >= min_score)

        return query.count()

    def update(self, job_id: int, data: JobUpdate) -> Optional[Job]:
        """Update job status and notes."""
        job = self.get_by_id(job_id)
        if not job:
            return None

        if data.status is not None:
            job.status = data.status
        if data.notes is not None:
            job.notes = data.notes

        job.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(job)
        return job

    def delete(self, job_id: int) -> bool:
        """Delete a job."""
        job = self.get_by_id(job_id)
        if not job:
            return False

        self.session.delete(job)
        self.session.commit()
        return True

    def exists(self, external_id: str, source: str, profile_id: int) -> bool:
        """Check if a job already exists for a profile."""
        return (
            self.session.query(Job)
            .filter(
                Job.external_id == external_id,
                Job.source == source,
                Job.profile_id == profile_id,
            )
            .first()
            is not None
        )

    def get_stats(self, profile_id: int) -> JobStats:
        """Get job statistics for a profile."""
        jobs = self.session.query(Job).filter(Job.profile_id == profile_id).all()

        if not jobs:
            return JobStats()

        total = len(jobs)
        scores = [j.match_score for j in jobs]
        avg_score = sum(scores) / total if total > 0 else 0.0

        status_counts = {}
        for job in jobs:
            status_counts[job.status] = status_counts.get(job.status, 0) + 1

        return JobStats(
            total_jobs=total,
            new_jobs=status_counts.get("new", 0),
            reviewing_jobs=status_counts.get("reviewing", 0),
            applied_jobs=status_counts.get("applied", 0),
            interview_jobs=status_counts.get("interview", 0),
            rejected_jobs=status_counts.get("rejected", 0),
            accepted_jobs=status_counts.get("accepted", 0),
            avg_match_score=round(avg_score, 3),
        )
