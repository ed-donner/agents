import pytest
from unittest.mock import Mock, patch
from src.services.ollama_service import OllamaService, OllamaResponse

class TestOllamaService:
    """Test cases for Ollama service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = OllamaService(
            base_url="http://localhost:11434",
            model="llama3.1:8b",
            timeout=30
        )
    
    @patch('src.services.ollama_service.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.service.test_connection()
        assert result is True
    
    @patch('src.services.ollama_service.requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed connection test."""
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.service.test_connection()
        assert result is False
    
    @patch('src.services.ollama_service.requests.get')
    def test_check_model_availability(self, mock_get):
        """Test model availability check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.1:8b:latest"},
                {"name": "other-model:latest"}
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.service.check_model_availability()
        assert result is True
    
    @patch('src.services.ollama_service.requests.post')
    def test_generate_sync_success(self, mock_post):
        """Test successful synchronous generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test response",
            "model": "llama3.1:8b",
            "total_duration": 1000000,
            "eval_count": 10
        }
        mock_post.return_value = mock_response
        
        result = self.service.generate_sync("Test prompt")
        
        assert isinstance(result, OllamaResponse)
        assert result.content == "This is a test response"
        assert result.model == "llama3.1:8b"
    
    @patch('src.services.ollama_service.requests.post')
    def test_generate_sync_failure(self, mock_post):
        """Test failed synchronous generation."""
        mock_post.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            self.service.generate_sync("Test prompt")
        
        assert "Error communicating with Ollama" in str(exc_info.value)
