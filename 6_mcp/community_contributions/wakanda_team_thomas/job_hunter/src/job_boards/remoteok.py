"""RemoteOK job board API client."""

from datetime import datetime, timezone
from typing import Any
from src.job_boards.base import JobBoardClient, JobBoardError
from src.schemas.job import JobBoardListing


class RemoteOKClient(JobBoardClient):
    """Client for RemoteOK API (https://remoteok.com)."""

    @property
    def source_name(self) -> str:
        return "remoteok"

    @property
    def base_url(self) -> str:
        return "https://remoteok.com/api"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        """
        Search RemoteOK for 100% remote worldwide jobs.
        Only jobs without geographic restrictions are included.
        """
        try:
            client = self.get_client()
            response = client.get(
                self.base_url,
                headers={"User-Agent": "JobHunter/1.0"}
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise JobBoardError(f"RemoteOK API request failed: {e}") from e

        if not isinstance(data, list) or len(data) == 0:
            return []

        data = data[1:]

        keywords_lower = [k.lower() for k in keywords]
        listings = []

        for job in data:
            if not self._is_worldwide_remote(job):
                continue

            if not self._matches_keywords(job, keywords_lower):
                continue

            listing = self._parse_job(job)
            if listing:
                listings.append(listing)

            if len(listings) >= limit:
                break

        return listings

    def _is_worldwide_remote(self, job: dict) -> bool:
        """Check if job is available worldwide (no geographic restrictions)."""
        location = job.get("location", "").lower()
        
        restricted_terms = [
            "usa only", "us only", "united states only",
            "uk only", "eu only", "europe only", "european",
            "canada only", "us/canada", "north america only",
            "apac only", "latam only", "emea only",
        ]
        
        for term in restricted_terms:
            if term in location:
                return False
        
        return True

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        """Check if job matches any of the keywords."""
        if not keywords_lower:
            return True

        searchable = " ".join([
            job.get("position", ""),
            job.get("company", ""),
            job.get("description", ""),
            " ".join(job.get("tags", [])),
        ]).lower()

        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
        """Parse RemoteOK job data into JobBoardListing."""
        try:
            job_id = str(job.get("id", ""))
            if not job_id:
                return None

            posted_at = None
            if "date" in job:
                try:
                    posted_at = datetime.fromisoformat(
                        job["date"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass

            tags = job.get("tags", [])
            skills = [tag for tag in tags if tag] if tags else []

            salary = None
            if job.get("salary_min") and job.get("salary_max"):
                salary = f"${job['salary_min']:,} - ${job['salary_max']:,}"
            elif job.get("salary_min"):
                salary = f"${job['salary_min']:,}+"

            return JobBoardListing(
                external_id=job_id,
                source=self.source_name,
                title=job.get("position", "Unknown Position"),
                company=job.get("company", "Unknown Company"),
                description=job.get("description", ""),
                required_skills=skills,
                salary_range=salary,
                url=job.get("url", f"https://remoteok.com/l/{job_id}"),
                posted_at=posted_at,
                location="Remote",
                is_remote=True,
            )
        except Exception:
            return None
