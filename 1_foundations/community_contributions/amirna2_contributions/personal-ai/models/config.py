from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatbotConfig:
    """Configuration for the career chatbot."""
    name: str
    github_username: Optional[str] = None
    resume_path: str = "me/resume.pdf"
    linkedin_path: str = "me/linkedin.pdf"
    summary_path: str = "me/summary.txt"
    model: str = "gpt-4o-mini-2024-07-18"  # Primary chat model
    evaluator_model: str = "gemini-2.5-flash"  # Evaluation model (different provider OK)
    job_matching_model: str = "gpt-4o-2024-08-06"  # Model for job matching analysis
    job_match_threshold: str = "Good"  # Minimum match level for contact facilitation
