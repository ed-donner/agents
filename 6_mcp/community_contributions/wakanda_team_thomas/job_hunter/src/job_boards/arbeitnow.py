"""Arbeitnow job board API client."""

from datetime import datetime
from typing import Any

from src.job_boards.base import JobBoardClient, JobBoardError
from src.schemas.job import JobBoardListing


class ArbeitnowClient(JobBoardClient):
    """Client for Arbeitnow API (https://arbeitnow.com)."""

    @property
    def source_name(self) -> str:
        return "arbeitnow"

    @property
    def base_url(self) -> str:
        return "https://www.arbeitnow.com/api/job-board-api"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        """
        Search Arbeitnow for remote jobs.
        
        Arbeitnow API supports remote filter.
        """
        try:
            client = self.get_client()
            response = client.get(self.base_url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise JobBoardError(f"Arbeitnow API request failed: {e}") from e

        jobs = data.get("data", [])
        if not jobs:
            return []

        keywords_lower = [k.lower() for k in keywords]
        listings = []

        for job in jobs:
            if not job.get("remote", False):
                continue

            if keywords_lower and not self._matches_keywords(job, keywords_lower):
                continue

            listing = self._parse_job(job)
            if listing:
                listings.append(listing)

            if len(listings) >= limit:
                break

        return listings

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        """Check if job matches any of the keywords."""
        if not keywords_lower:
            return True

        searchable = " ".join([
            job.get("title", ""),
            job.get("company_name", ""),
            job.get("description", ""),
            " ".join(job.get("tags", [])),
        ]).lower()

        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
        """Parse Arbeitnow job data into JobBoardListing."""
        try:
            slug = job.get("slug", "")
            if not slug:
                return None

            posted_at = None
            if "created_at" in job:
                try:
                    timestamp = job["created_at"]
                    if isinstance(timestamp, (int, float)):
                        posted_at = datetime.fromtimestamp(timestamp)
                    else:
                        posted_at = datetime.fromisoformat(
                            str(timestamp).replace("Z", "+00:00")
                        )
                except (ValueError, TypeError):
                    pass

            tags = job.get("tags", [])
            skills = [tag for tag in tags if tag] if tags else []

            return JobBoardListing(
                external_id=slug,
                source=self.source_name,
                title=job.get("title", "Unknown Position"),
                company=job.get("company_name", "Unknown Company"),
                description=job.get("description", ""),
                required_skills=skills,
                salary_range=None,
                url=job.get("url", f"https://arbeitnow.com/view/{slug}"),
                posted_at=posted_at,
                location="Remote",
                is_remote=True,
            )
        except Exception:
            return None
