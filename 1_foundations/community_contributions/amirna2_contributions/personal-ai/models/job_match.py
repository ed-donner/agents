from typing import List, Optional
from pydantic import BaseModel


class SkillAssessment(BaseModel):
    """Assessment of a specific skill."""
    skill: str
    level: str  # "Extensive", "Solid", "Moderate", "Limited", "Inferred", "Missing"
    evidence: str  # Where this skill was found or reasoning for inference


class JobMatchResult(BaseModel):
    """Result of job matching analysis."""
    overall_match_level: str  # Very Strong, Strong, Good, Moderate, Weak, Very Weak
    skill_assessments: List[SkillAssessment]
    experience_analysis: str
    industry_analysis: str
    recommendations: str
    should_facilitate_contact: bool
    contact_reason: Optional[str] = None
