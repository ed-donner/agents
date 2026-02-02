"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# Set test environment
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    with patch("config.llm_config.get_llm") as mock:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Test response")
        mock.return_value = mock_llm
        yield mock_llm


@pytest.fixture
def sample_request():
    """Sample project request for testing"""
    from models.requirements import ComplexStackRequest
    
    return ComplexStackRequest(
        project_name="Test Project",
        description="A test project",
        backend_language="python",
        backend_framework="FastAPI",
        frontend_framework="react"
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)
