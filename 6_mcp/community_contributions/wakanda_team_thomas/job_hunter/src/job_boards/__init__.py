"""Job board API clients in a single module."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import httpx

from src.schemas import JobBoardListing


class JobBoardError(Exception):
    """Raised when job board API request fails."""


class JobBoardClient(ABC):
    """Abstract base class for job board API clients."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass

    @abstractmethod
    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        pass

    def get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RemoteOKClient(JobBoardClient):
    @property
    def source_name(self) -> str:
        return "remoteok"

    @property
    def base_url(self) -> str:
        return "https://remoteok.com/api"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        try:
            client = self.get_client()
            response = client.get(self.base_url, headers={"User-Agent": "JobHunter/1.0"})
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
        location = job.get("location", "").lower()
        restricted_terms = [
            "usa only",
            "us only",
            "united states only",
            "uk only",
            "eu only",
            "europe only",
            "european",
            "canada only",
            "us/canada",
            "north america only",
            "apac only",
            "latam only",
            "emea only",
        ]
        return not any(term in location for term in restricted_terms)

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        if not keywords_lower:
            return True
        searchable = " ".join(
            [
                job.get("position", ""),
                job.get("company", ""),
                job.get("description", ""),
                " ".join(job.get("tags", [])),
            ]
        ).lower()
        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
        try:
            job_id = str(job.get("id", ""))
            if not job_id:
                return None
            posted_at = None
            if "date" in job:
                try:
                    posted_at = datetime.fromisoformat(job["date"].replace("Z", "+00:00"))
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


class RemotiveClient(JobBoardClient):
    @property
    def source_name(self) -> str:
        return "remotive"

    @property
    def base_url(self) -> str:
        return "https://remotive.com/api/remote-jobs"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
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
        location = job.get("candidate_required_location", "").lower()
        if not location or location in ["worldwide", "anywhere", "global", ""]:
            return True
        restricted_terms = [
            "usa only",
            "us only",
            "united states only",
            "united states",
            "uk only",
            "eu only",
            "europe only",
            "european union",
            "canada only",
            "north america only",
            "apac only",
            "latam only",
            "emea only",
        ]
        if any(term in location for term in restricted_terms):
            return False
        return "only" not in location

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        if not keywords_lower:
            return True
        searchable = " ".join(
            [
                job.get("title", ""),
                job.get("company_name", ""),
                job.get("description", ""),
                " ".join(job.get("tags", [])),
                job.get("category", ""),
            ]
        ).lower()
        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
        try:
            job_id = str(job.get("id", ""))
            if not job_id:
                return None
            posted_at = None
            if "publication_date" in job:
                try:
                    posted_at = datetime.fromisoformat(
                        job["publication_date"].replace("Z", "+00:00")
                    )
                except (ValueError, TypeError):
                    pass
            tags = job.get("tags", [])
            skills = [tag for tag in tags if tag] if tags else []
            if job.get("category"):
                skills.append(job["category"])
            return JobBoardListing(
                external_id=job_id,
                source=self.source_name,
                title=job.get("title", "Unknown Position"),
                company=job.get("company_name", "Unknown Company"),
                description=job.get("description", ""),
                required_skills=skills,
                salary_range=job.get("salary") or None,
                url=job.get("url", ""),
                posted_at=posted_at,
                location="Remote",
                is_remote=True,
            )
        except Exception:
            return None


class ArbeitnowClient(JobBoardClient):
    @property
    def source_name(self) -> str:
        return "arbeitnow"

    @property
    def base_url(self) -> str:
        return "https://www.arbeitnow.com/api/job-board-api"

    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
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
        location = job.get("location", "").lower()
        if not location or location in ["worldwide", "anywhere", "global", "remote"]:
            return True
        restricted_terms = [
            "usa only",
            "us only",
            "united states only",
            "uk only",
            "eu only",
            "europe only",
            "germany only",
            "canada only",
            "north america only",
        ]
        return not any(term in location for term in restricted_terms)

    def _matches_keywords(self, job: dict, keywords_lower: list[str]) -> bool:
        if not keywords_lower:
            return True
        searchable = " ".join(
            [
                job.get("title", ""),
                job.get("company_name", ""),
                job.get("description", ""),
                " ".join(job.get("tags", [])),
            ]
        ).lower()
        return any(kw in searchable for kw in keywords_lower)

    def _parse_job(self, job: dict) -> JobBoardListing | None:
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
                        posted_at = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
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

__all__ = [
    "JobBoardClient",
    "JobBoardError",
    "RemoteOKClient",
    "RemotiveClient",
    "ArbeitnowClient",
]


def get_all_clients() -> list[type[JobBoardClient]]:
    """Return all available job board client classes."""
    return [
        RemoteOKClient,
        RemotiveClient,
        ArbeitnowClient,
    ]
