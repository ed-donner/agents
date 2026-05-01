
import os
import json
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Job Hunt Server")


applications_db: list[dict] = []


#  Tool 1: Search Jobs 

@mcp.tool()
def search_jobs(role: str, location: str, remote_ok: bool = True) -> str:
    """Search for job listings by role and location.
    In production, this would connect to LinkedIn, Indeed, or other job APIs.
    For now it returns realistic sample listings to demonstrate the pipeline."""

   
    sample_jobs = [
        {
            "title": f"Senior {role}",
            "company": "TechNova AI",
            "location": location if not remote_ok else f"{location} (Remote)",
            "salary_range": "$120k - $160k",
            "requirements": ["3+ years Python", "ML/DL frameworks", "Cloud deployment", "Docker"],
            "posted": "2 days ago",
            "url": "https://example.com/job/1"
        },
        {
            "title": role,
            "company": "DataForge Labs",
            "location": location,
            "salary_range": "$90k - $130k",
            "requirements": ["2+ years experience", "PyTorch or TensorFlow", "REST APIs", "SQL"],
            "posted": "5 days ago",
            "url": "https://example.com/job/2"
        },
        {
            "title": f"Junior {role}",
            "company": "Bright Systems",
            "location": "Remote",
            "salary_range": "$70k - $100k",
            "requirements": ["Python", "Basic ML knowledge", "API development", "Git"],
            "posted": "1 day ago",
            "url": "https://example.com/job/3"
        },
        {
            "title": f"Lead {role}",
            "company": "Sentinel AI",
            "location": location,
            "salary_range": "$150k - $200k",
            "requirements": ["5+ years ML experience", "Team leadership", "MLOps", "Production systems", "Computer vision"],
            "posted": "3 days ago",
            "url": "https://example.com/job/4"
        }
    ]

    return json.dumps({"query": f"{role} in {location}", "results": sample_jobs, "total": len(sample_jobs)})


# Tool 2: Match CV 

@mcp.tool()
def match_cv_to_job(job_requirements: str, candidate_skills: str) -> str:
    """Score how well a candidate's skills match a job's requirements.
    Takes the job requirements and candidate skills as comma-separated strings.
    Returns a match analysis with score and gaps."""

    job_reqs = [r.strip().lower() for r in job_requirements.split(",")]
    cand_skills = [s.strip().lower() for s in candidate_skills.split(",")]

    matched = []
    missing = []

    for req in job_reqs:
        found = False
        for skill in cand_skills:
            if req in skill or skill in req:
                matched.append(req)
                found = True
                break
        if not found:
            missing.append(req)

    total = len(job_reqs)
    match_count = len(matched)
    score = round((match_count / total) * 100) if total > 0 else 0

    if score >= 80:
        verdict = "Strong match — apply with confidence"
    elif score >= 60:
        verdict = "Decent match — highlight transferable skills"
    elif score >= 40:
        verdict = "Partial match — address gaps in cover letter"
    else:
        verdict = "Weak match — consider upskilling first"

    return json.dumps({
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "verdict": verdict
    })


# Tool 3: Draft Application 

@mcp.tool()
def draft_cover_letter(job_title: str, company: str, candidate_name: str,
                       candidate_background: str, matched_skills: str,
                       missing_skills: str) -> str:
    """Generate a cover letter draft based on match analysis.
    The agent should use an LLM to polish this — this provides the structure."""

    letter = f"""Dear Hiring Team at {company},

I'm {candidate_name}, and I'm reaching out about the {job_title} position.

My background in {candidate_background} aligns well with what you're looking for.
Specifically, I bring experience in: {matched_skills}.

{"I'm actively building skills in: " + missing_skills + "." if missing_skills else ""}

I'd welcome the chance to discuss how my experience could contribute to {company}'s goals.

Best regards,
{candidate_name}"""

    return json.dumps({
        "draft": letter,
        "note": "This is a structured draft. The agent should use an LLM to make it more natural and specific."
    })


# Tool 4: Track Applications 

@mcp.tool()
def save_application(job_title: str, company: str, match_score: int,
                     status: str = "drafted") -> str:
    """Save a job application to the tracker.
    Status can be: drafted, applied, interviewing, offered, rejected."""

    entry = {
        "id": len(applications_db) + 1,
        "job_title": job_title,
        "company": company,
        "match_score": match_score,
        "status": status,
        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    applications_db.append(entry)

    return json.dumps({"saved": True, "entry": entry, "total_tracked": len(applications_db)})


@mcp.tool()
def list_applications() -> str:
    """List all tracked job applications with their current status."""
    if not applications_db:
        return json.dumps({"applications": [], "message": "No applications tracked yet."})

    summary = {
        "total": len(applications_db),
        "by_status": {},
        "applications": applications_db
    }

    for app in applications_db:
        status = app["status"]
        summary["by_status"][status] = summary["by_status"].get(status, 0) + 1

    return json.dumps(summary)


@mcp.tool()
def update_application_status(application_id: int, new_status: str) -> str:
    """Update the status of a tracked application.
    Status options: drafted, applied, interviewing, offered, rejected."""

    for app in applications_db:
        if app["id"] == application_id:
            old_status = app["status"]
            app["status"] = new_status
            return json.dumps({
                "updated": True,
                "company": app["company"],
                "old_status": old_status,
                "new_status": new_status
            })

    return json.dumps({"updated": False, "error": f"Application {application_id} not found"})


#  Tool 5: Job Hunt Stats 

@mcp.tool()
def get_hunt_stats() -> str:
    """Get statistics about your job hunt progress."""
    if not applications_db:
        return json.dumps({"message": "No applications tracked yet. Start applying!"})

    total = len(applications_db)
    statuses = {}
    scores = []
    companies = []

    for app in applications_db:
        statuses[app["status"]] = statuses.get(app["status"], 0) + 1
        scores.append(app["match_score"])
        companies.append(app["company"])

    avg_score = round(sum(scores) / len(scores)) if scores else 0

    return json.dumps({
        "total_applications": total,
        "status_breakdown": statuses,
        "avg_match_score": avg_score,
        "highest_match": max(scores) if scores else 0,
        "companies_applied_to": companies
    })


if __name__ == "__main__":
    mcp.run()
