"""
job_search.py — Scout stage: search JobSpy (LinkedIn + Indeed) and deduplicate results.

Usage as a script:
    uv run python job_search.py

Usage as a module (e.g. from a notebook):
    from job_search import run_scout
    raw_jobs = await run_scout()
"""

import json
import re
import asyncio
from pathlib import Path
from difflib import SequenceMatcher

from agents.mcp import MCPServerStdio


# --- Configuration ---

from user_config import get_config

_cfg = get_config()
SEARCH_TERMS = _cfg.search.terms
LOCATION = _cfg.search.location
RESULTS_PER_CALL = _cfg.search.results_per_call
HOURS_OLD = _cfg.search.hours_old
CLIENT_TIMEOUT_SECONDS = 180
RAW_JOBS_PATH = Path("jobs_raw.json")
DEDUP_TITLE_THRESHOLD = 0.85
MAX_SNIPPET_CHARS = 400


# --- Normalization helpers ---

def normalize_job(job: dict, max_desc_chars: int = MAX_SNIPPET_CHARS) -> dict:
    """Convert a raw JobSpy job dict into our lightweight normalized schema.

    Keeps the FULL untruncated description (full_description) alongside the
    short snippet. This matters most for LinkedIn postings: Firecrawl does not
    support scraping linkedin.com ("we do not support this website"), so the
    Evaluator stage falls back to full_description for LinkedIn jobs instead of
    firecrawl_scrape. JobSpy already fetches the full LinkedIn description at
    search time via linkedin_fetch_description=True, so this data is available
    for free at this stage.
    """
    desc = job.get("description") or job.get("job_description") or ""
    return {
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "url": job.get("url") or job.get("job_url"),
        "salary": job.get("salary") or job.get("salary_source"),
        "date_posted": job.get("date_posted"),
        "snippet": desc[:max_desc_chars].strip(),
        "full_description": desc.strip(),
    }


def normalize_text(s: str) -> str:
    """Lowercase, strip parenthetical suffixes like (m/w/d) and punctuation."""
    s = (s or "").lower()
    s = re.sub(r"\(.*?\)", "", s)
    s = re.sub(r"[^\w\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


# --- Search ---

async def _search_site(server: MCPServerStdio, site_name: str, term: str, extra_params: dict) -> list[dict]:
    """Run a single search_jobs call and return normalized jobs."""
    print(f"🔍 {site_name.capitalize()}: {term}")
    params = {
        "site_name": [site_name],
        "search_term": term,
        "location": LOCATION,
        "results_wanted": RESULTS_PER_CALL,
        "hours_old": HOURS_OLD,
        **extra_params,
    }
    result = await server.call_tool("search_jobs", params)
    payload = json.loads(result.content[0].text)
    jobs = payload.get("jobs", payload) if isinstance(payload, dict) else payload
    print(f"   → {len(jobs)} jobs")
    return [normalize_job(job) for job in jobs]


async def search_jobspy() -> list[dict]:
    """Search LinkedIn and Indeed across all SEARCH_TERMS, dedup by URL, return job list."""
    jobs_by_url: dict[str, dict] = {}

    async with MCPServerStdio(
        name="JobSpy",
        params={"command": "uvx", "args": ["jobspy-mcp"]},
        client_session_timeout_seconds=CLIENT_TIMEOUT_SECONDS,
    ) as server:

        for term in SEARCH_TERMS:
            for norm in await _search_site(server, "linkedin", term, {"linkedin_fetch_description": True}):
                if norm["url"]:
                    jobs_by_url[norm["url"]] = norm

        for term in SEARCH_TERMS:
            for norm in await _search_site(server, "indeed", term, {"country_indeed": "Germany"}):
                if norm["url"]:
                    jobs_by_url[norm["url"]] = norm

    return list(jobs_by_url.values())


# --- Deduplication ---

def dedup_cross_site(jobs: list[dict], title_threshold: float = DEDUP_TITLE_THRESHOLD):
    """Dedup jobs across sites by (company + fuzzy title match). Returns (kept, removed_pairs)."""
    deduped, removed, seen = [], [], []

    for job in jobs:
        norm_title = normalize_text(job["title"])
        norm_company = normalize_text(job.get("company") or "")

        is_dupe = False
        for seen_job, seen_title, seen_company in seen:
            if norm_company == seen_company:
                similarity = SequenceMatcher(None, norm_title, seen_title).ratio()
                if similarity >= title_threshold:
                    is_dupe = True
                    removed.append((job, seen_job, similarity))
                    break

        if not is_dupe:
            deduped.append(job)
            seen.append((job, norm_title, norm_company))

    return deduped, removed


def print_removed_pairs(removed_pairs: list[tuple]) -> None:
    print(f"\nRemoved {len(removed_pairs)} duplicates:\n")
    for dupe, original, sim in removed_pairs:
        print(f"  [{sim:.2f}] REMOVED: \"{dupe['title']}\" ({dupe['url']})")
        print(f"         KEPT:    \"{original['title']}\" ({original['url']})\n")


# --- File I/O ---

def save_jobs(jobs: list[dict], path: Path = RAW_JOBS_PATH) -> None:
    path.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


def load_jobs(path: Path = RAW_JOBS_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


# --- Orchestration ---

async def run_scout(save: bool = True) -> list[dict]:
    """Full scout pipeline: search, dedup, optionally save. Returns deduplicated job list."""
    raw_jobs = await search_jobspy()
    print(f"\n💾 Search complete: {len(raw_jobs)} unique-by-URL jobs")

    print(f"Before cross-site dedup: {len(raw_jobs)}")
    deduped_jobs, removed_pairs = dedup_cross_site(raw_jobs)
    print(f"After cross-site dedup: {len(deduped_jobs)}")
    print_removed_pairs(removed_pairs)

    if save:
        save_jobs(deduped_jobs)
        print(f"💾 Saved {len(deduped_jobs)} deduplicated jobs → {RAW_JOBS_PATH}")

    for i, job in enumerate(deduped_jobs[:10], 1):
        print(f"  {i:>2}. {job['title']} @ {job['company']} — {job['location']}")

    return deduped_jobs


def main():
    asyncio.run(run_scout())


if __name__ == "__main__":
    main()
