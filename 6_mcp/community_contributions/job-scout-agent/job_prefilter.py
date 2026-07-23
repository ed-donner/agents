"""
job_prefilter.py — Prefilter stage: score raw jobs for relevance using a lightweight,
tool-free LLM pass (title + company + location + short snippet only).

Usage as a script:
    uv run python job_prefilter.py

Usage as a module (e.g. from a notebook):
    from job_prefilter import run_prefilter
    shortlisted_jobs = await run_prefilter()
"""

import json
from pathlib import Path

from agents import Agent, Runner


# --- Configuration ---

from user_config import get_config

_cfg = get_config()
RAW_JOBS_PATH = Path("jobs_raw.json")
SHORTLIST_PATH = Path("jobs_shortlisted.json")
CRITERIA_PATH = _cfg.criteria_path
MODEL = "gpt-4.1-mini"
SHORTLIST_MIN_SIZE = _cfg.prefilter.shortlist_min_size  # rank used to determine the score threshold

# Short profile summary for prefilter, authored by the user in config.yaml —
# full profile.md is reserved for the in-depth Evaluator stage
PROFILE_SUMMARY = _cfg.get_profile_summary()


# --- File I/O ---

def load_raw_jobs(path: Path = RAW_JOBS_PATH) -> list[dict]:
    jobs = json.loads(path.read_text(encoding="utf-8"))
    print(f"✅ Loaded {len(jobs)} jobs from {path}")
    return jobs


def save_shortlist(jobs: list[dict], path: Path = SHORTLIST_PATH) -> None:
    path.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Prompt construction ---

def build_compact_jobs(raw_jobs: list[dict]) -> list[dict]:
    return [
        {
            "idx": i,
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "snippet": j.get("snippet", ""),
        }
        for i, j in enumerate(raw_jobs)
    ]


def build_prefilter_instructions(compact_jobs: list[dict], criteria: str) -> str:
    return f"""
You are scoring job postings for RELEVANCE before full evaluation.
You have title, company, location, and a SHORT (often truncated) snippet — NOT the full posting.

For EVERY job in the list, assign a relevance_score from 0 to 10:
- 0-2: Clearly disqualifying — junior/intern/Werkstudent title, purely Sales/Marketing role,
       explicit mandatory native German with no flexibility, or location entirely outside Germany
- 3-5: Unclear/ambiguous — generic title, truncated snippet, unclear seniority or domain,
       but no explicit disqualifying signal
- 6-8: Plausible match — title aligns with target roles, no disqualifying signal, some
       relevant domain/industry signal in the snippet
- 9-10: Strong match — title and snippet both align well with target roles and preferred
       industries/domains

Do NOT exclude anything yourself — score every single job, even ones that seem irrelevant.
Err toward the middle of the range (3-6) when the snippet gives insufficient information —
do not default to 0-2 just because you're unsure.

Return ONLY a JSON array of objects, one per job, in the same order as the input:
[{{"idx": 0, "score": 7}}, {{"idx": 1, "score": 2}}, ...]

--- CANDIDATE PROFILE SUMMARY ---
{PROFILE_SUMMARY}

--- JOB SEARCH CRITERIA ---
{criteria}

--- JOB LIST ({len(compact_jobs)} items) ---
{json.dumps(compact_jobs, ensure_ascii=False)}
"""


# --- Response parsing ---

def parse_json_array(text: str) -> list:
    """Parse a JSON array from agent text, tolerating markdown fences and preamble."""
    raw = (text or "").strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1]
        if raw.lstrip().startswith("json"):
            raw = raw.lstrip()[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("["), raw.rfind("]") + 1
        return json.loads(raw[start:end])


# --- Scoring + shortlisting ---

def apply_scores(raw_jobs: list[dict], scores: list[dict]) -> list[dict]:
    """Attach relevance_score to each job in place, defaulting to neutral (5) if missing."""
    score_map = {
        s["idx"]: s["score"]
        for s in scores
        if isinstance(s, dict) and "idx" in s and "score" in s
    }
    for i, job in enumerate(raw_jobs):
        job["relevance_score"] = score_map.get(i, 5)
    return raw_jobs


def shortlist_by_score(raw_jobs: list[dict], min_size: int = SHORTLIST_MIN_SIZE) -> list[dict]:
    """Sort by relevance_score desc and keep all jobs tied with the job at rank `min_size`."""
    sorted_all = sorted(raw_jobs, key=lambda j: j["relevance_score"], reverse=True)

    if len(sorted_all) > min_size:
        threshold_score = sorted_all[min_size - 1]["relevance_score"]
    else:
        threshold_score = 0

    shortlisted = [j for j in sorted_all if j["relevance_score"] >= threshold_score]
    print(f"Threshold score: {threshold_score}")
    print(f"Shortlisted (score >= {threshold_score}): {len(shortlisted)} jobs\n")

    for i, j in enumerate(shortlisted, 1):
        print(f"  {i:>2}. [{j['relevance_score']}] {j['title']} @ {j['company']}")

    return shortlisted


# --- Orchestration ---

async def run_prefilter(save: bool = True) -> list[dict]:
    """Full prefilter pipeline: load raw jobs, score via LLM, shortlist, optionally save."""
    raw_jobs = load_raw_jobs()
    criteria = CRITERIA_PATH.read_text(encoding="utf-8")

    compact_jobs = build_compact_jobs(raw_jobs)
    instructions = build_prefilter_instructions(compact_jobs, criteria)

    prefilter_agent = Agent(name="Prefilter", instructions=instructions, model=MODEL)

    print("🔍 Running pre-filter agent (scoring mode)...")
    result = await Runner.run(prefilter_agent, "Return the scores now.")
    print("✅ Scoring complete.")

    scores = parse_json_array(result.final_output)
    raw_jobs = apply_scores(raw_jobs, scores)
    shortlisted_jobs = shortlist_by_score(raw_jobs)

    if save:
        save_shortlist(shortlisted_jobs)
        print(f"\n💾 Saved {len(shortlisted_jobs)} shortlisted jobs → {SHORTLIST_PATH}")

    return shortlisted_jobs


def main():
    import asyncio
    asyncio.run(run_prefilter())


if __name__ == "__main__":
    main()
