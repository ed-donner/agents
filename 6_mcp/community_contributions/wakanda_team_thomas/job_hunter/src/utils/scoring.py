"""Scoring utilities for job-profile matching."""

from dataclasses import dataclass
from src.config import MatchWeights


@dataclass
class MatchResult:
    """Result of matching a job against a profile."""

    score: float
    skills_score: float
    experience_score: float
    keywords_score: float
    requirements_score: float
    matched_skills: list[str]
    missing_skills: list[str]

    @property
    def meets_threshold(self) -> bool:
        """Check if score meets the 90% threshold."""
        return self.score >= 0.90


def normalize_skill(skill: str) -> str:
    """Normalize a skill string for comparison."""
    return skill.lower().strip().replace("-", " ").replace("_", " ")


def extract_skill_names(skills: list[dict]) -> set[str]:
    """Extract normalized skill names from skill objects."""
    return {normalize_skill(s.get("name", "")) for s in skills if s.get("name")}


def calculate_skills_match(
    profile_skills: list[dict],
    job_skills: list[str],
) -> tuple[float, list[str], list[str]]:
    """
    Calculate skill match score between profile and job.
    
    Returns:
        Tuple of (score, matched_skills, missing_skills)
    """
    if not job_skills:
        return 1.0, [], []

    profile_skill_names = extract_skill_names(profile_skills)
    job_skill_names = {normalize_skill(s) for s in job_skills}

    matched = []
    missing = []

    for job_skill in job_skills:
        normalized = normalize_skill(job_skill)
        
        found = False
        for profile_skill in profile_skill_names:
            if normalized in profile_skill or profile_skill in normalized:
                found = True
                break
        
        if found:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    if not job_skill_names:
        return 1.0, matched, missing

    score = len(matched) / len(job_skill_names)
    return score, matched, missing


def calculate_experience_match(
    profile_experience: list[dict],
    job_title: str,
    job_description: str,
) -> float:
    """
    Calculate experience relevance score.
    
    Checks if profile experience aligns with job requirements.
    """
    if not profile_experience:
        return 0.5

    job_text = f"{job_title} {job_description}".lower()

    seniority_keywords = {
        "senior": ["senior", "sr.", "lead", "principal", "staff"],
        "mid": ["mid", "intermediate", "regular"],
        "junior": ["junior", "jr.", "entry", "associate", "graduate"],
    }

    job_level = "mid"
    for level, keywords in seniority_keywords.items():
        if any(kw in job_text for kw in keywords):
            job_level = level
            break

    profile_titles = [exp.get("title", "").lower() for exp in profile_experience]
    profile_level = "mid"
    
    for title in profile_titles:
        for level, keywords in seniority_keywords.items():
            if any(kw in title for kw in keywords):
                profile_level = level
                break

    level_scores = {
        ("senior", "senior"): 1.0,
        ("senior", "mid"): 0.7,
        ("senior", "junior"): 0.4,
        ("mid", "senior"): 0.9,
        ("mid", "mid"): 1.0,
        ("mid", "junior"): 0.7,
        ("junior", "senior"): 0.6,
        ("junior", "mid"): 0.8,
        ("junior", "junior"): 1.0,
    }

    base_score = level_scores.get((job_level, profile_level), 0.7)

    relevance_boost = 0.0
    for exp in profile_experience:
        title = exp.get("title", "").lower()
        description = exp.get("description", "").lower()
        
        job_keywords = set(job_text.split())
        exp_text = f"{title} {description}"
        
        common = sum(1 for kw in job_keywords if len(kw) > 3 and kw in exp_text)
        if common > 5:
            relevance_boost = min(0.2, common * 0.02)
            break

    return min(1.0, base_score + relevance_boost)


def calculate_keywords_match(
    profile_keywords: list[str],
    job_description: str,
) -> float:
    """
    Calculate keyword overlap between profile and job description.
    """
    if not profile_keywords:
        return 0.5

    job_text = job_description.lower()
    matched = sum(1 for kw in profile_keywords if kw.lower() in job_text)

    if not profile_keywords:
        return 0.5

    return matched / len(profile_keywords)


def calculate_requirements_match(
    profile_skills: list[dict],
    profile_experience: list[dict],
    job_description: str,
) -> float:
    """
    Calculate how well profile meets job requirements.
    
    Analyzes job description for requirement patterns.
    """
    job_text = job_description.lower()

    requirement_patterns = [
        "required", "must have", "minimum", "at least",
        "years of experience", "experience with", "proficient in",
    ]

    has_requirements = any(pattern in job_text for pattern in requirement_patterns)
    if not has_requirements:
        return 0.8

    profile_text = " ".join([
        " ".join(s.get("name", "") for s in profile_skills),
        " ".join(exp.get("title", "") + " " + exp.get("description", "") 
                 for exp in profile_experience),
    ]).lower()

    requirement_sections = []
    for pattern in requirement_patterns:
        if pattern in job_text:
            start = job_text.find(pattern)
            end = min(start + 200, len(job_text))
            requirement_sections.append(job_text[start:end])

    if not requirement_sections:
        return 0.8

    matches = 0
    total = 0
    
    for section in requirement_sections:
        words = [w for w in section.split() if len(w) > 4]
        for word in words[:10]:
            total += 1
            if word in profile_text:
                matches += 1

    if total == 0:
        return 0.8

    return matches / total


def calculate_match_score(
    profile_skills: list[dict],
    profile_experience: list[dict],
    profile_keywords: list[str],
    job_title: str,
    job_description: str,
    job_required_skills: list[str],
) -> MatchResult:
    """
    Calculate overall match score between profile and job.
    
    Uses weighted combination of:
    - Skills match (40%)
    - Experience match (25%)
    - Keywords match (20%)
    - Requirements match (15%)
    
    Returns MatchResult with scores and details.
    """
    skills_score, matched_skills, missing_skills = calculate_skills_match(
        profile_skills, job_required_skills
    )

    experience_score = calculate_experience_match(
        profile_experience, job_title, job_description
    )

    keywords_score = calculate_keywords_match(
        profile_keywords, job_description
    )

    requirements_score = calculate_requirements_match(
        profile_skills, profile_experience, job_description
    )

    weighted_score = (
        skills_score * MatchWeights.SKILLS
        + experience_score * MatchWeights.EXPERIENCE
        + keywords_score * MatchWeights.KEYWORDS
        + requirements_score * MatchWeights.REQUIREMENTS
    )

    return MatchResult(
        score=round(weighted_score, 3),
        skills_score=round(skills_score, 3),
        experience_score=round(experience_score, 3),
        keywords_score=round(keywords_score, 3),
        requirements_score=round(requirements_score, 3),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
    )
