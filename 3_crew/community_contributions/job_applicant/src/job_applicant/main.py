#!/usr/bin/env python
"""
Multi-Agent Automated Job Application System

Pipeline:
1. Research Crew: Parse resume → Search jobs → Match & rank
2. Application Crew (per job): Tailor resume → Write cover letter → Submit application
"""

import json
import os
import sys
import warnings
from datetime import datetime

from .crews.research_crew import ResearchCrew
from .crews.application_crew import ApplicationCrew
from .state import ApplicationStateManager

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Base directory for the job_applicant project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(
    resume_path: str,
    keywords: list[str],
    locations: list[str] = None,
    platforms: list[str] = None,
    job_types: list[str] = None,
    min_match_score: float = 0.5,
):
    """
    Run the full automated job application pipeline.

    Args:
        resume_path: Path to the candidate's resume (PDF/DOCX)
        keywords: Job search keywords
        locations: Target locations (default: ["Remote"])
        platforms: Platforms to search (default: all)
        job_types: Job types to search (default: ["Full-time"])
        min_match_score: Minimum match score to apply (default: 0.5)
    """
    locations = locations or ["Remote"]
    platforms = platforms or ["linkedin", "indeed", "glassdoor", "ziprecruiter"]
    job_types = job_types or ["Full-time"]

    state = ApplicationStateManager(db_path=os.path.join(BASE_DIR, "output", "applications.db"))

    print("=" * 60)
    print("  AUTOMATED JOB APPLICATION SYSTEM")
    print("=" * 60)
    print(f"\nResume: {resume_path}")
    print(f"Keywords: {', '.join(keywords)}")
    print(f"Locations: {', '.join(locations)}")
    print(f"Platforms: {', '.join(platforms)}")
    print(f"Min match score: {min_match_score}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Phase 1: Research Crew ──────────────────────────────────
    print("=" * 60)
    print("  PHASE 1: RESEARCH (Parse → Search → Match)")
    print("=" * 60)

    research_inputs = {
        "resume_path": resume_path,
        "keywords": json.dumps(keywords),
        "locations": json.dumps(locations),
        "platforms": json.dumps(platforms),
        "job_types": json.dumps(job_types),
        "current_date": str(datetime.now()),
    }

    research_crew = ResearchCrew()
    research_crew.resume_path = resume_path
    research_result = research_crew.crew().kickoff(inputs=research_inputs)

    # Extract matched jobs from result
    matched_jobs = []
    try:
        if hasattr(research_result, 'pydantic') and research_result.pydantic:
            matched_jobs = [m.model_dump() for m in research_result.pydantic.matches]
        elif hasattr(research_result, 'json_dict') and research_result.json_dict:
            data = research_result.json_dict
            matched_jobs = data.get("matches", [data] if isinstance(data, dict) else data)
        else:
            raw = research_result.raw
            try:
                data = json.loads(raw)
                matched_jobs = data.get("matches", [data] if isinstance(data, dict) else data)
            except json.JSONDecodeError:
                print(f"\nResearch crew output (raw):\n{raw[:500]}")
    except Exception as e:
        print(f"\nError parsing research results: {e}")
        print(f"Raw result: {research_result.raw[:500] if hasattr(research_result, 'raw') else str(research_result)[:500]}")

    # Filter by minimum score and save to state
    qualified_jobs = []
    for match in matched_jobs:
        job = match.get("job", match)
        score = match.get("score", 0.5)

        if score >= min_match_score:
            state.save_job(job, score=score, recommendation=match.get("recommendation", "Apply"))
            if not state.is_already_applied(job.get("url", "")):
                qualified_jobs.append(match)

    print(f"\n{'=' * 60}")
    print(f"  RESEARCH COMPLETE")
    print(f"  Total matches: {len(matched_jobs)}")
    print(f"  Qualified (score >= {min_match_score}): {len(qualified_jobs)}")
    print(f"  Already applied (skipping): {len(matched_jobs) - len(qualified_jobs)}")
    print(f"{'=' * 60}\n")

    if not qualified_jobs:
        print("No qualified jobs to apply to. Try broadening your search.")
        return state.get_stats()

    # ── Phase 2: Application Crew (per job) ─────────────────────
    print("=" * 60)
    print("  PHASE 2: APPLICATIONS (Tailor → Cover Letter → Apply)")
    print("=" * 60)

    # Extract candidate profile from research results
    profile_path = os.path.join(BASE_DIR, "output", "candidate_profile.json")
    candidate_profile = ""
    candidate_name = ""
    candidate_email = ""
    candidate_phone = ""

    if os.path.exists(profile_path):
        with open(profile_path, "r") as f:
            profile_data = json.load(f)
            candidate_profile = json.dumps(profile_data, indent=2)
            candidate_name = profile_data.get("name", "")
            candidate_email = profile_data.get("email", "")
            candidate_phone = profile_data.get("phone", "")

    for i, match in enumerate(qualified_jobs, 1):
        job = match.get("job", match)
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")
        url = job.get("url", "")
        platform = job.get("platform", "generic")

        print(f"\n--- Application {i}/{len(qualified_jobs)}: {title} at {company} ---")
        print(f"    Score: {match.get('score', 'N/A')} | Platform: {platform}")
        print(f"    URL: {url}")

        try:
            app_inputs = {
                "candidate_profile": candidate_profile,
                "candidate_name": candidate_name,
                "candidate_email": candidate_email,
                "candidate_phone": candidate_phone,
                "job_title": title,
                "company_name": company,
                "job_description": job.get("description", ""),
                "job_requirements": json.dumps(job.get("requirements", [])),
                "matching_skills": json.dumps(match.get("matching_skills", [])),
                "job_url": url,
                "platform": platform,
                "resume_path": resume_path,
                "current_date": str(datetime.now()),
            }

            app_result = ApplicationCrew().crew().kickoff(inputs=app_inputs)

            # Parse application result
            status = "submitted"
            error_msg = None
            try:
                if hasattr(app_result, 'raw'):
                    result_data = json.loads(app_result.raw)
                    status = result_data.get("status", "submitted")
                    error_msg = result_data.get("error")
            except (json.JSONDecodeError, AttributeError):
                pass

            state.save_application(
                job_url=url,
                status=status,
                error_message=error_msg,
            )

            print(f"    Result: {status.upper()}")
            if error_msg:
                print(f"    Note: {error_msg}")

        except Exception as e:
            print(f"    FAILED: {str(e)}")
            state.save_application(
                job_url=url,
                status="failed",
                error_message=str(e),
            )

    # ── Summary ─────────────────────────────────────────────────
    stats = state.get_stats()
    print(f"\n{'=' * 60}")
    print("  PIPELINE COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Jobs discovered: {stats['total_jobs_discovered']}")
    print(f"  Applications submitted: {stats['submitted']}")
    print(f"  Applications failed: {stats['failed']}")
    print(f"  Applications blocked: {stats['blocked']}")
    print(f"  Platform breakdown: {stats['by_platform']}")
    print(f"{'=' * 60}\n")

    return stats


def main():
    """CLI entry point with default configuration."""
    resume_path = os.path.join(BASE_DIR, "resumes", "resume.pdf")

    if len(sys.argv) > 1:
        resume_path = sys.argv[1]

    if not os.path.exists(resume_path):
        print(f"Error: Resume not found at '{resume_path}'")
        print(f"Place your resume in: {os.path.join(BASE_DIR, 'resumes', '')}")
        print(f"Or provide a path: python -m job_applicant.main /path/to/resume.pdf")
        sys.exit(1)

    keywords = ["software engineer", "python developer", "backend engineer"]
    locations = ["Remote", "San Francisco, CA"]

    if len(sys.argv) > 2:
        keywords = sys.argv[2].split(",")
    if len(sys.argv) > 3:
        locations = sys.argv[3].split(",")

    run(
        resume_path=resume_path,
        keywords=keywords,
        locations=locations,
    )


if __name__ == "__main__":
    main()
