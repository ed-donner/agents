"""Tests for configuration module."""

import pytest
from src.config import (
    Settings,
    JobStatus,
    JobSource,
    MatchWeights,
    get_settings,
)


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.job_match_threshold == 0.90
        assert settings.search_interval_hours == 24
        assert settings.debug is False
        assert settings.log_level == "INFO"

    def test_langfuse_disabled_by_default(self):
        """Test Langfuse is disabled when keys not set."""
        settings = Settings()
        assert settings.langfuse_enabled is False

    def test_langfuse_enabled_with_keys(self, monkeypatch):
        """Test Langfuse is enabled when keys are set."""
        monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
        monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
        settings = Settings()
        assert settings.langfuse_enabled is True

    def test_database_path_extraction(self):
        """Test database path extraction from URL."""
        settings = Settings(database_url="sqlite:///./test.db")
        assert settings.database_path.name == "test.db"


class TestJobStatus:
    """Test JobStatus constants."""

    def test_all_statuses(self):
        """Test all status values are in ALL list."""
        assert JobStatus.NEW in JobStatus.ALL
        assert JobStatus.REVIEWING in JobStatus.ALL
        assert JobStatus.APPLIED in JobStatus.ALL
        assert JobStatus.INTERVIEW in JobStatus.ALL
        assert JobStatus.REJECTED in JobStatus.ALL
        assert JobStatus.ACCEPTED in JobStatus.ALL
        assert len(JobStatus.ALL) == 6


class TestJobSource:
    """Test JobSource constants."""

    def test_all_sources(self):
        """Test all source values are in ALL list."""
        assert JobSource.REMOTEOK in JobSource.ALL
        assert JobSource.REMOTIVE in JobSource.ALL
        assert JobSource.ARBEITNOW in JobSource.ALL
        assert len(JobSource.ALL) == 3


class TestMatchWeights:
    """Test MatchWeights constants."""

    def test_weights_sum_to_one(self):
        """Test matching weights sum to 1.0."""
        total = (
            MatchWeights.SKILLS
            + MatchWeights.EXPERIENCE
            + MatchWeights.KEYWORDS
            + MatchWeights.REQUIREMENTS
        )
        assert total == pytest.approx(1.0)


class TestGetSettings:
    """Test get_settings function."""

    def test_returns_settings_instance(self):
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_caching(self):
        """Test settings are cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
