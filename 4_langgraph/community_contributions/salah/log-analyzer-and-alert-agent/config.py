from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os


class LogAnalyzerConfig(BaseModel):
    logs_directory: str = Field(
        default="logs",
        description="Directory containing log files to analyze"
    )

    source_code_directory: str = Field(
        default="source_code",
        description="Directory containing application source code for investigation"
    )

    error_patterns: List[str] = Field(
        default=["ERROR", "FATAL", "Exception", "Traceback"],
        description="String patterns to identify error entries in logs"
    )

    severity_levels: Dict[str, int] = Field(
        default={"FATAL": 1, "ERROR": 2, "WARN": 3, "INFO": 4},
        description="Priority ranking for log levels (lower number = higher priority)"
    )

    max_errors_to_analyze: int = Field(
        default=5,
        description="Maximum number of errors to analyze in one session",
        ge=1,
        le=20
    )

    enable_notifications: bool = Field(
        default=True,
        description="Send push notifications for critical errors"
    )

    enable_source_investigation: bool = Field(
        default=True,
        description="Search and analyze source code when errors reference files"
    )

    enable_browser_tools: bool = Field(
        default=False,
        description="Enable Playwright browser tools for web navigation (requires 'playwright install chromium')"
    )

    llm_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for worker and evaluator"
    )

    def get_absolute_logs_path(self) -> str:
        if os.path.isabs(self.logs_directory):
            return self.logs_directory
        return os.path.abspath(self.logs_directory)

    def get_absolute_source_path(self) -> str:
        if os.path.isabs(self.source_code_directory):
            return self.source_code_directory
        return os.path.abspath(self.source_code_directory)

    def validate_directories(self) -> Dict[str, bool]:
        logs_exists = os.path.isdir(self.get_absolute_logs_path())
        source_exists = os.path.isdir(self.get_absolute_source_path())

        return {
            "logs_directory_exists": logs_exists,
            "source_code_directory_exists": source_exists
        }

    def get_error_pattern_regex(self) -> str:
        return '|'.join(self.error_patterns)

    class Config:
        json_schema_extra = {
            "example": {
                "logs_directory": "logs",
                "source_code_directory": "source_code",
                "error_patterns": ["ERROR", "FATAL", "Exception"],
                "severity_levels": {"FATAL": 1, "ERROR": 2, "WARN": 3},
                "max_errors_to_analyze": 5,
                "enable_notifications": True,
                "enable_source_investigation": True,
                "llm_model": "gpt-4o-mini"
            }
        }
