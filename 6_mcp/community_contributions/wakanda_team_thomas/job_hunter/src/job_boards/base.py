"""Base class for job board API clients."""

from abc import ABC, abstractmethod
from typing import Optional

import httpx

from src.schemas.job import JobBoardListing


class JobBoardError(Exception):
    """Raised when job board API request fails."""
    pass


class JobBoardClient(ABC):
    """Abstract base class for job board API clients."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the job board source identifier."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the API base URL."""
        pass

    @abstractmethod
    def search(self, keywords: list[str], limit: int = 50) -> list[JobBoardListing]:
        """
        Search for remote jobs matching the given keywords.
        
        Args:
            keywords: List of search keywords (skills, job titles, etc.)
            limit: Maximum number of results to return.
            
        Returns:
            List of job listings from this board.
        """
        pass

    def get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
