import os
from typing import Optional
try:
    from pydantic import BaseSettings, Field
except ImportError:
    from pydantic_settings import BaseSettings
    from pydantic import Field

class Config(BaseSettings):
    """Configuration management for the transcript summarizer application."""
    
    # Provider Configuration
    llm_provider: str = Field(
        default="ollama",
        env="LLM_PROVIDER",
        description="LLM provider to use (e.g., 'ollama', 'gemini')"
    )

    # Ollama Configuration
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        env="OLLAMA_BASE_URL",
        description="Base URL for Ollama API"
    )
    
    ollama_model_name: str = Field(
        default="llama3.1:8b",
        env="OLLAMA_MODEL_NAME",
        description="Name of the Ollama model to use"
    )

    # Gemini Configuration
    gemini_api_key: Optional[str] = Field(
        default=None,
        env="GEMINI_API_KEY",
        description="API key for Google Gemini"
    )

    gemini_model_name: str = Field(
        default="gemini-2.5-flash",
        env="GEMINI_MODEL_NAME",
        description="Name of the Gemini model to use"
    )
    
    # Chunking Configuration
    chunk_size: int = Field(
        default=2000,
        env="CHUNK_SIZE",
        description="Maximum tokens per chunk"
    )
    
    chunk_overlap: int = Field(
        default=200,
        env="CHUNK_OVERLAP",
        description="Token overlap between chunks"
    )
    
    # Gradio Configuration
    gradio_port: int = Field(
        default=7860,
        env="GRADIO_PORT",
        description="Port for Gradio server"
    )
    
    # Processing Configuration
    max_concurrent_requests: int = Field(
        default=3,
        env="MAX_CONCURRENT_REQUESTS",
        description="Maximum concurrent API requests"
    )
    
    request_timeout: int = Field(
        default=300,
        env="REQUEST_TIMEOUT",
        description="Request timeout in seconds"
    )
    
    # Temperature for LLM
    temperature: float = Field(
        default=0.3,
        env="TEMPERATURE",
        description="Temperature for text generation"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global config instance
config = Config()
