"""Remotive job board API client."""

from datetime import datetime
from typing import Any
from src.job_boards.base import JobBoardClient, JobBoardError
from src.schemas.job import JobBoardListing


class RemotiveClient(JobBoardClient):
    """Client for Remotive API (https://remotive.com)."""

    @property
    def source_name(self) -> str:
        return "remotive"

    @property
    def base_url(self) -> str:
        return "https://remotive.com/api/remote-jobs"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        """
        Search Remotive for 100% remote worldwide jobs.
        Only jobs without geographic restrictions are included.
        """
        try:
            client = self.get_client()
            params = {"limit": min(limit * 2, 100)}
            if keywords:
                params["search"] = " ".join(keywords[:3])

            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise JobBoardError(f"Remotive API request failed: {e}") from e

        jobs = data.get("jobs", [])
        if not jobs:
            return []

        keywords_lower = [k.lower() for k in keywords]
        listings = []

        for job in jobs:
            if not self._is_worldwide_remote(job):
                continue

            if keywords_lower and not self._matches_keywords(job, keywords_lower):
                continue

            listing = self._parse_job(job)
            if listing:
                listings.append(listing)

            if len(listings) >= limit:
                break

        return listings

    def _is_worldwide_remote(self, job: dict) -> bool:
        """Check if job is available worldwide (no geographic restrictions)."""
        location = job.get("candidate_required_location", "").lower()
        
        if not location or location in ["worldwide", "anywhere", "global", ""]:
            return True
        
        restricted_terms = [
            "usa only", "us only", "united states only", "united states",
            "uk only", "eu only", "europe only", "european union",
            "canada only", "north america only",
            "apac only", "latam only", "emea only",
        ]
        
        for term in restricted_terms:
            if term in location:
                return False
        
        if location and "only" in location:
            return False
        
        return True

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        """Check if job matches any of the keywords."""
        if not keywords_lower:
            return True

        searchable = " ".join([
            job.get("title", ""),
            job.get("company_name", ""),
            job.get("description", ""),
            " ".join(job.get("tags", [])),
            job.get("category", ""),
        ]).lower()

        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
        """Parse Remotive job data into JobBoardListing."""
        try:
            job_id = str(job.get("id", ""))
            if not job_id:
                return None

            posted_at = None
            if "publication_date" in job:
                try:
                    date_str = job["publication_date"]
                    posted_at = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            tags = job.get("tags", [])
            skills = [tag for tag in tags if tag] if tags else []
            
            if job.get("category"):
                skills.append(job["category"])

            salary = job.get("salary") or None

            return JobBoardListing(
                external_id=job_id,
                source=self.source_name,
                title=job.get("title", "Unknown Position"),
                company=job.get("company_name", "Unknown Company"),
                description=job.get("description", ""),
                required_skills=skills,
                salary_range=salary,
                url=job.get("url", ""),
                posted_at=posted_at,
                location="Remote",
                is_remote=True,
            )
        except Exception:
            return None
