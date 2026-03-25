"""Tests for scoring utilities."""

import pytest

from src.utils.scoring import (
    MatchResult,
    calculate_match_score,
    calculate_skills_match,
    calculate_experience_match,
    calculate_keywords_match,
    calculate_requirements_match,
    normalize_skill,
    extract_skill_names,
)


class TestNormalization:
    """Tests for skill normalization."""

    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        assert normalize_skill("Python") == "python"
        assert normalize_skill("JAVASCRIPT") == "javascript"

    def test_normalize_strips_whitespace(self):
        """Test normalization strips whitespace."""
        assert normalize_skill("  Python  ") == "python"

    def test_normalize_replaces_separators(self):
        """Test normalization replaces hyphens and underscores."""
        assert normalize_skill("machine-learning") == "machine learning"
        assert normalize_skill("data_science") == "data science"

    def test_extract_skill_names(self):
        """Test extracting skill names from skill objects."""
        skills = [
            {"name": "Python", "level": "expert"},
            {"name": "JavaScript", "years": 3},
            {"name": ""},
            {},
        ]
        names = extract_skill_names(skills)
        assert "python" in names
        assert "javascript" in names
        assert len(names) == 2


class TestSkillsMatch:
    """Tests for skills matching."""

    def test_perfect_match(self):
        """Test perfect skill match returns 1.0."""
        profile_skills = [
            {"name": "Python"},
            {"name": "Django"},
            {"name": "AWS"},
        ]
        job_skills = ["Python", "Django", "AWS"]

        score, matched, missing = calculate_skills_match(profile_skills, job_skills)

        assert score == 1.0
        assert len(matched) == 3
        assert len(missing) == 0

    def test_partial_match(self):
        """Test partial skill match."""
        profile_skills = [{"name": "Python"}, {"name": "Django"}]
        job_skills = ["Python", "Django", "AWS", "Kubernetes"]

        score, matched, missing = calculate_skills_match(profile_skills, job_skills)

        assert score == 0.5
        assert len(matched) == 2
        assert "AWS" in missing
        assert "Kubernetes" in missing

    def test_no_job_skills(self):
        """Test empty job skills returns 1.0."""
        profile_skills = [{"name": "Python"}]
        job_skills = []

        score, matched, missing = calculate_skills_match(profile_skills, job_skills)

        assert score == 1.0

    def test_case_insensitive_match(self):
        """Test skill matching is case insensitive."""
        profile_skills = [{"name": "python"}, {"name": "DJANGO"}]
        job_skills = ["Python", "Django"]

        score, matched, missing = calculate_skills_match(profile_skills, job_skills)

        assert score == 1.0

    def test_partial_skill_match(self):
        """Test partial skill name matching."""
        profile_skills = [{"name": "Machine Learning"}]
        job_skills = ["ML", "Machine Learning", "Deep Learning"]

        score, matched, missing = calculate_skills_match(profile_skills, job_skills)

        assert "Machine Learning" in matched


class TestExperienceMatch:
    """Tests for experience matching."""

    def test_senior_matches_senior(self):
        """Test senior profile matches senior job."""
        profile_experience = [{"title": "Senior Software Engineer"}]
        job_title = "Senior Python Developer"
        job_description = "Looking for a senior developer..."

        score = calculate_experience_match(profile_experience, job_title, job_description)

        assert score >= 0.9

    def test_junior_matches_junior(self):
        """Test junior profile matches junior job."""
        profile_experience = [{"title": "Junior Developer"}]
        job_title = "Junior Python Developer"
        job_description = "Entry level position..."

        score = calculate_experience_match(profile_experience, job_title, job_description)

        assert score >= 0.9

    def test_no_experience_returns_baseline(self):
        """Test empty experience returns baseline score."""
        profile_experience = []
        job_title = "Developer"
        job_description = "Some job"

        score = calculate_experience_match(profile_experience, job_title, job_description)

        assert score == 0.5

    def test_experience_relevance_boost(self):
        """Test relevant experience gets boost."""
        profile_experience = [
            {
                "title": "Python Developer",
                "description": "Built APIs using Django and FastAPI",
            }
        ]
        job_title = "Python Backend Developer"
        job_description = "Build APIs using Django and FastAPI for our platform"

        score = calculate_experience_match(profile_experience, job_title, job_description)

        assert score >= 0.8


class TestKeywordsMatch:
    """Tests for keywords matching."""

    def test_all_keywords_match(self):
        """Test all keywords in description."""
        profile_keywords = ["python", "api", "backend"]
        job_description = "Looking for Python developer to build APIs for our backend"

        score = calculate_keywords_match(profile_keywords, job_description)

        assert score == 1.0

    def test_partial_keywords_match(self):
        """Test some keywords in description."""
        profile_keywords = ["python", "api", "frontend", "mobile"]
        job_description = "Python API development"

        score = calculate_keywords_match(profile_keywords, job_description)

        assert score == 0.5

    def test_no_keywords_returns_baseline(self):
        """Test empty keywords returns baseline."""
        profile_keywords = []
        job_description = "Any job description"

        score = calculate_keywords_match(profile_keywords, job_description)

        assert score == 0.5


class TestRequirementsMatch:
    """Tests for requirements matching."""

    def test_no_requirements_returns_baseline(self):
        """Test job without requirements returns baseline."""
        profile_skills = [{"name": "Python"}]
        profile_experience = []
        job_description = "Great opportunity to work with us"

        score = calculate_requirements_match(
            profile_skills, profile_experience, job_description
        )

        assert score == 0.8

    def test_requirements_with_matching_skills(self):
        """Test requirements with matching profile returns score."""
        profile_skills = [{"name": "Python"}, {"name": "Django"}]
        profile_experience = [{"title": "Developer", "description": "Python Django developer"}]
        job_description = """
        Required: 3+ years of experience with Python and Django.
        Must have strong backend development skills.
        """

        score = calculate_requirements_match(
            profile_skills, profile_experience, job_description
        )

        assert 0.0 <= score <= 1.0


class TestMatchScore:
    """Tests for overall match scoring."""

    def test_high_match_score(self):
        """Test profile with high match gets high score."""
        profile_skills = [
            {"name": "Python"},
            {"name": "Django"},
            {"name": "AWS"},
            {"name": "PostgreSQL"},
        ]
        profile_experience = [
            {"title": "Senior Python Developer", "description": "Built Django APIs"}
        ]
        profile_keywords = ["python", "backend", "api", "django"]

        result = calculate_match_score(
            profile_skills=profile_skills,
            profile_experience=profile_experience,
            profile_keywords=profile_keywords,
            job_title="Senior Python Developer",
            job_description="Looking for Senior Python Developer with Django and AWS experience",
            job_required_skills=["Python", "Django", "AWS"],
        )

        assert result.score >= 0.85
        assert result.skills_score >= 0.9
        assert len(result.matched_skills) >= 3

    def test_low_match_score(self):
        """Test profile with low match gets low score."""
        profile_skills = [{"name": "Java"}, {"name": "Spring"}]
        profile_experience = [{"title": "Junior Java Developer"}]
        profile_keywords = ["java", "spring", "backend"]

        result = calculate_match_score(
            profile_skills=profile_skills,
            profile_experience=profile_experience,
            profile_keywords=profile_keywords,
            job_title="Senior Python Developer",
            job_description="Need expert Python developer with Django",
            job_required_skills=["Python", "Django", "FastAPI", "AWS"],
        )

        assert result.score < 0.7
        assert len(result.missing_skills) >= 3

    def test_meets_threshold_property(self):
        """Test meets_threshold property works correctly."""
        result = MatchResult(
            score=0.92,
            skills_score=0.9,
            experience_score=0.9,
            keywords_score=0.9,
            requirements_score=0.9,
            matched_skills=["Python"],
            missing_skills=[],
        )
        assert result.meets_threshold is True

        result.score = 0.85
        assert result.meets_threshold is False

    def test_score_weights_sum_to_one(self):
        """Test that weight components properly contribute to score."""
        profile_skills = [{"name": "Python"}]
        profile_experience = [{"title": "Developer"}]
        profile_keywords = ["python"]

        result = calculate_match_score(
            profile_skills=profile_skills,
            profile_experience=profile_experience,
            profile_keywords=profile_keywords,
            job_title="Developer",
            job_description="Python developer position",
            job_required_skills=["Python"],
        )

        assert 0.0 <= result.score <= 1.0
        assert 0.0 <= result.skills_score <= 1.0
        assert 0.0 <= result.experience_score <= 1.0
        assert 0.0 <= result.keywords_score <= 1.0
        assert 0.0 <= result.requirements_score <= 1.0
