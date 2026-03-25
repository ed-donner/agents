"""Tests for job board API clients."""

from unittest.mock import Mock, patch

import pytest

from src.job_boards import (
    JobBoardClient,
    JobBoardError,
    RemoteOKClient,
    RemotiveClient,
    ArbeitnowClient,
    get_all_clients,
)
from src.schemas.job import JobBoardListing


class TestJobBoardBase:
    """Tests for base JobBoardClient."""

    def test_get_all_clients(self):
        """Test get_all_clients returns all clients."""
        clients = get_all_clients()
        assert len(clients) == 3
        
        sources = {c.source_name for c in clients}
        assert sources == {"remoteok", "remotive", "arbeitnow"}

    def test_client_context_manager(self):
        """Test client can be used as context manager."""
        with RemoteOKClient() as client:
            assert client.source_name == "remoteok"


class TestRemoteOKClient:
    """Tests for RemoteOK client."""

    def test_source_name(self):
        """Test source name is correct."""
        client = RemoteOKClient()
        assert client.source_name == "remoteok"

    def test_base_url(self):
        """Test base URL is correct."""
        client = RemoteOKClient()
        assert client.base_url == "https://remoteok.com/api"

    def test_parse_job_complete(self):
        """Test parsing complete job data."""
        client = RemoteOKClient()
        job_data = {
            "id": "123456",
            "position": "Python Developer",
            "company": "Tech Corp",
            "description": "Great opportunity for Python developers",
            "tags": ["python", "django", "aws"],
            "url": "https://remoteok.com/l/123456",
            "date": "2026-03-20T10:00:00Z",
            "salary_min": 100000,
            "salary_max": 150000,
        }
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "123456"
        assert listing.source == "remoteok"
        assert listing.title == "Python Developer"
        assert listing.company == "Tech Corp"
        assert "python" in listing.required_skills
        assert listing.salary_range == "$100,000 - $150,000"
        assert listing.is_remote is True

    def test_parse_job_minimal(self):
        """Test parsing minimal job data."""
        client = RemoteOKClient()
        job_data = {"id": "789"}
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "789"
        assert listing.title == "Unknown Position"

    def test_parse_job_invalid(self):
        """Test parsing invalid job data returns None."""
        client = RemoteOKClient()
        
        assert client._parse_job({}) is None
        assert client._parse_job({"id": ""}) is None

    def test_matches_keywords(self):
        """Test keyword matching."""
        client = RemoteOKClient()
        job_data = {
            "position": "Senior Python Developer",
            "company": "Acme Inc",
            "description": "Looking for Django experience",
            "tags": ["python", "django"],
        }
        
        assert client._matches_keywords(job_data, ["python"]) is True
        assert client._matches_keywords(job_data, ["django"]) is True
        assert client._matches_keywords(job_data, ["java"]) is False
        assert client._matches_keywords(job_data, []) is True

    @patch("src.job_boards.remoteok.RemoteOKClient.get_client")
    def test_search_success(self, mock_get_client):
        """Test successful search."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {"legal": "info"},
            {"id": "1", "position": "Python Dev", "company": "Co", "tags": ["python"]},
            {"id": "2", "position": "Java Dev", "company": "Co", "tags": ["java"]},
        ]
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        client = RemoteOKClient()
        results = client.search(["python"], limit=10)
        
        assert len(results) == 1
        assert results[0].title == "Python Dev"


class TestRemotiveClient:
    """Tests for Remotive client."""

    def test_source_name(self):
        """Test source name is correct."""
        client = RemotiveClient()
        assert client.source_name == "remotive"

    def test_base_url(self):
        """Test base URL is correct."""
        client = RemotiveClient()
        assert client.base_url == "https://remotive.com/api/remote-jobs"

    def test_parse_job_complete(self):
        """Test parsing complete job data."""
        client = RemotiveClient()
        job_data = {
            "id": 456789,
            "title": "Backend Engineer",
            "company_name": "Startup XYZ",
            "description": "Build scalable APIs",
            "tags": ["python", "fastapi"],
            "category": "Software Development",
            "url": "https://remotive.com/job/456789",
            "publication_date": "2026-03-18T08:00:00Z",
            "salary": "$120k - $160k",
        }
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "456789"
        assert listing.source == "remotive"
        assert listing.title == "Backend Engineer"
        assert listing.company == "Startup XYZ"
        assert "python" in listing.required_skills
        assert "Software Development" in listing.required_skills
        assert listing.salary_range == "$120k - $160k"

    def test_parse_job_minimal(self):
        """Test parsing minimal job data."""
        client = RemotiveClient()
        job_data = {"id": 123}
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "123"

    @patch("src.job_boards.remotive.RemotiveClient.get_client")
    def test_search_with_keywords(self, mock_get_client):
        """Test search passes keywords to API."""
        mock_response = Mock()
        mock_response.json.return_value = {"jobs": []}
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        client = RemotiveClient()
        client.search(["python", "django"], limit=20)
        
        call_args = mock_client.get.call_args
        assert "search" in call_args.kwargs["params"]


class TestArbeitnowClient:
    """Tests for Arbeitnow client."""

    def test_source_name(self):
        """Test source name is correct."""
        client = ArbeitnowClient()
        assert client.source_name == "arbeitnow"

    def test_base_url(self):
        """Test base URL is correct."""
        client = ArbeitnowClient()
        assert client.base_url == "https://www.arbeitnow.com/api/job-board-api"

    def test_parse_job_complete(self):
        """Test parsing complete job data."""
        client = ArbeitnowClient()
        job_data = {
            "slug": "python-developer-abc123",
            "title": "Python Developer",
            "company_name": "Remote Co",
            "description": "Work from anywhere",
            "tags": ["python", "remote"],
            "url": "https://arbeitnow.com/view/python-developer-abc123",
            "remote": True,
            "created_at": 1710936000,
        }
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "python-developer-abc123"
        assert listing.source == "arbeitnow"
        assert listing.title == "Python Developer"
        assert listing.company == "Remote Co"

    def test_parse_job_minimal(self):
        """Test parsing minimal job data."""
        client = ArbeitnowClient()
        job_data = {"slug": "job-123"}
        
        listing = client._parse_job(job_data)
        
        assert listing is not None
        assert listing.external_id == "job-123"

    def test_parse_job_no_slug(self):
        """Test parsing job without slug returns None."""
        client = ArbeitnowClient()
        
        assert client._parse_job({}) is None
        assert client._parse_job({"slug": ""}) is None

    @patch("src.job_boards.arbeitnow.ArbeitnowClient.get_client")
    def test_search_filters_remote_only(self, mock_get_client):
        """Test search only returns remote jobs."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"slug": "1", "title": "Remote Job", "remote": True, "tags": ["python"]},
                {"slug": "2", "title": "Office Job", "remote": False, "tags": ["python"]},
                {"slug": "3", "title": "Another Remote", "remote": True, "tags": ["python"]},
            ]
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        client = ArbeitnowClient()
        results = client.search(["python"], limit=10)
        
        assert len(results) == 2
        assert all(r.is_remote for r in results)


class TestJobBoardError:
    """Tests for JobBoardError."""

    def test_error_message(self):
        """Test error contains message."""
        error = JobBoardError("API failed")
        assert str(error) == "API failed"

    @patch("src.job_boards.remoteok.RemoteOKClient.get_client")
    def test_api_error_wrapped(self, mock_get_client):
        """Test API errors are wrapped in JobBoardError."""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_get_client.return_value = mock_client
        
        client = RemoteOKClient()
        
        with pytest.raises(JobBoardError, match="RemoteOK API request failed"):
            client.search(["python"])
