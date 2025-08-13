#!/usr/bin/env python3
"""
Test script to verify .env file loading
"""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config

def test_env_loading():
    """Test if .env file values are being loaded correctly."""
    print("🔍 Testing .env file loading...")
    
    # Create config instance
    config = Config()
    
    print("\n📊 Configuration Values:")
    print(f"  LLM_PROVIDER: {config.llm_provider}")
    print(f"  OLLAMA_BASE_URL: {config.ollama_base_url}")
    print(f"  OLLAMA_MODEL_NAME: {config.ollama_model_name}")
    print(f"  GEMINI_API_KEY: {'Set' if config.gemini_api_key else 'Not Set'}")
    print(f"  GEMINI_MODEL_NAME: {config.gemini_model_name}")
    print(f"  CHUNK_SIZE: {config.chunk_size}")
    print(f"  CHUNK_OVERLAP: {config.chunk_overlap}")
    print(f"  TEMPERATURE: {config.temperature}")
    print(f"  GRADIO_PORT: {config.gradio_port}")
    print(f"  MAX_CONCURRENT_REQUESTS: {config.max_concurrent_requests}")
    print(f"  REQUEST_TIMEOUT: {config.request_timeout}")
    print(f"  LOG_LEVEL: {config.log_level}")
    
    # Check if values match what we set in .env
    expected_values = {
        'chunk_size': 2500,
        'chunk_overlap': 1500,
        'temperature': 0.6,
        'gradio_port': 7862,
        'max_concurrent_requests': 5,
        'request_timeout': 400,
        'log_level': 'DEBUG'  # Add expected log level
    }
    
    print("\n🔍 Verification:")
    all_correct = True
    for key, expected in expected_values.items():
        actual = getattr(config, key)
        status = "✅" if actual == expected else "❌"
        print(f"  {key}: {actual} (expected {expected}) {status}")
        if actual != expected:
            all_correct = False
    
    print(f"\n🏁 Result: {'✅ All values loaded correctly from .env!' if all_correct else '❌ Some values not loaded from .env'}")
    
    # Also check environment variables directly
    print("\n🌍 Environment Variables:")
    env_vars = ['LLM_PROVIDER', 'OLLAMA_BASE_URL', 'OLLAMA_MODEL_NAME', 'GEMINI_API_KEY', 'GEMINI_MODEL_NAME',
                'CHUNK_SIZE', 'CHUNK_OVERLAP', 'TEMPERATURE', 'GRADIO_PORT', 
                'MAX_CONCURRENT_REQUESTS', 'REQUEST_TIMEOUT', 'LOG_LEVEL']
    
    for var in env_vars:
        value = os.getenv(var, 'Not set')
        print(f"  {var}: {value}")

def test_config_defaults():
    """Test that config loads with default values when no .env file exists."""
    # This will test the default values
    config = Config()
    
    # Test that we get some expected default values
    assert config.llm_provider == "ollama"
    assert config.ollama_base_url == "http://localhost:11434"
    assert config.ollama_model_name == "llama3.1:8b"
    assert config.gemini_api_key is None
    assert config.gemini_model_name == "gemini-2.5-flash"
    assert isinstance(config.temperature, float)
    assert isinstance(config.chunk_size, int)
    assert isinstance(config.chunk_overlap, int)

def test_config_types():
    """Test that config values have correct types."""
    config = Config()
    
    assert isinstance(config.llm_provider, str)
    assert isinstance(config.ollama_base_url, str)
    assert isinstance(config.ollama_model_name, str)
    assert isinstance(config.gemini_api_key, (str, type(None)))
    assert isinstance(config.gemini_model_name, str)
    assert isinstance(config.chunk_size, int)
    assert isinstance(config.chunk_overlap, int)
    assert isinstance(config.temperature, float)
    assert isinstance(config.gradio_port, int)
    assert isinstance(config.max_concurrent_requests, int)
    assert isinstance(config.request_timeout, int)
    assert isinstance(config.log_level, str)

if __name__ == "__main__":
    test_env_loading()
