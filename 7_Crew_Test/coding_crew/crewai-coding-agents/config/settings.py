"""
Global settings and configuration management
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class EnvironmentType(str, Enum):
    """Deployment environment types"""
    CLOUD = "cloud"
    ONPREM = "onprem"
    HYBRID = "hybrid"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentRole(str, Enum):
    """Available agent roles"""
    TEAM_MANAGER = "team_manager"
    ANALYST = "analyst"
    BACKEND_PYTHON = "backend_python"
    BACKEND_GO = "backend_go"
    BACKEND_NODEJS = "backend_nodejs"
    BACKEND_CSHARP = "backend_csharp"
    BACKEND_RUBY = "backend_ruby"
    FRONTEND_REACT = "frontend_react"
    FRONTEND_ANGULAR = "frontend_angular"
    FRONTEND_NEXTJS = "frontend_nextjs"
    DEVOPS = "devops"
    SYSTEM_ENGINEER = "system_engineer"
    CLOUD_ENGINEER = "cloud_engineer"
    DB_ENGINEER = "db_engineer"
    QA_ENGINEER = "qa_engineer"
    SECURITY_ENGINEER = "security_engineer"


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="gpt-4-turbo-preview", alias="DEFAULT_LLM_MODEL")
    default_temperature: float = Field(default=0.7, alias="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(default=4096, alias="DEFAULT_MAX_TOKENS")
    
    # CrewAI Settings
    crewai_verbose: bool = Field(default=True, alias="CREWAI_VERBOSE")
    crewai_memory: bool = Field(default=True, alias="CREWAI_MEMORY")
    crewai_max_rpm: int = Field(default=10, alias="CREWAI_MAX_RPM")
    
    # Application Settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: str = Field(default="./output", alias="OUTPUT_DIR")
    template_dir: str = Field(default="./templates", alias="TEMPLATE_DIR")
    
    # Optional Services
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
