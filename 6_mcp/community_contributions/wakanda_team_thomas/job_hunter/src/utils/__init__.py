"""Utility functions for the job hunting system."""

from src.utils.extractors import (
    MAX_FILE_SIZE_BYTES,
    ExtractionError,
    extract_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    get_supported_extensions,
    is_supported_file,
    validate_file_size,
)
from src.utils.scoring import (
    MatchResult,
    calculate_match_score,
    calculate_skills_match,
    calculate_experience_match,
    calculate_keywords_match,
    calculate_requirements_match,
    normalize_skill,
)

__all__ = [
    "MAX_FILE_SIZE_BYTES",
    "ExtractionError",
    "extract_text",
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "get_supported_extensions",
    "is_supported_file",
    "validate_file_size",
    "MatchResult",
    "calculate_match_score",
    "calculate_skills_match",
    "calculate_experience_match",
    "calculate_keywords_match",
    "calculate_requirements_match",
    "normalize_skill",
]
