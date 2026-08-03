"""
job_evaluator.py — Evaluator stage: Read through each job and its full description and score each
shortlisted job in depth against the candidate's full profile and criteria, in batches.

Usage as a script:
    uv run python job_evaluator.py

Usage as a module (e.g. from a notebook):
    from job_evaluator import run_evaluator
    final_ranked = await run_evaluator()
"""

import asyncio
import json
import re
from pathlib import Path

from agents import Agent, Runner
from openai import RateLimitError


# --- Configuration ---

from user_config import get_config

_cfg = get_config()
SHORTLIST_PATH = Path("jobs_shortlisted.json")
PROFILE_PATH = _cfg.profile_path
CRITERIA_PATH = _cfg.criteria_path
RANKED_PATH = Path("jobs_ranked.json")

MODEL = "gpt-5-mini"
BATCH_SIZE = 8          # gpt-5-mini's higher TPM limit (500K/min on tier 1) comfortably supports larger batches
MAX_TURNS_PER_BATCH = 30
CLIENT_TIMEOUT_SECONDS = 90
TOP_N = _cfg.evaluator.top_n

# --- Rate-limit handling ---
BATCH_DELAY_SECONDS = 0     # no throttle needed at this TPM tier; kept as a knob in case limits tighten
MAX_RETRIES = 5
RETRY_BASE_DELAY_SECONDS = 10  # exponential backoff base: 10s, 20s, 40s, 80s, 160s


# --- File I/O ---

def load_shortlisted_jobs(path: Path = SHORTLIST_PATH) -> list[dict]:
    jobs = json.loads(path.read_text(encoding="utf-8"))
    for i, job in enumerate(jobs):
        job["_global_idx"] = i
    return jobs



def load_profile_and_criteria() -> tuple[str, str]:
    profile = PROFILE_PATH.read_text(encoding="utf-8")
    criteria = CRITERIA_PATH.read_text(encoding="utf-8")
    return profile, criteria


def save_ranked_jobs(jobs: list[dict], path: Path = RANKED_PATH) -> None:
    path.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Prompt construction ---

def build_evaluator_instructions(batch: list[dict], profile: str, criteria: str) -> str:
    compact = [
        {
            "idx": j["_global_idx"], "title": j["title"], "company": j["company"],
            "location": j["location"], "url": j["url"],
            "full_description": j.get("full_description") or j.get("snippet", ""),
        }
        for j in batch
    ]

    return f"""
Evaluate each of the {len(batch)} jobs below against the candidate profile and search criteria.
Return one result for every job; do not skip any.

Use only the provided full_description for each job. Do not fetch or scrape anything.

Procedure:
1. Identify hard must-haves vs nice-to-haves.
   - Treat a requirement as hard only if it is clearly mandatory in tone or appears under headings
     like Required, Must have, Requirements, or mandatory Qualifications.
   - Treat sections such as Preferred, Nice to have, Bonus, What will help you, or similarly soft
     phrasing as non-gating unless the text clearly says they are required.
   - If the posting explicitly welcomes applicants who do not meet all listed requirements, do not
     apply the score caps below; evaluate overall fit more holistically.

2. For each hard must-have, classify profile evidence as exactly one of:
   - direct: clearly demonstrated in the profile
   - adjacent: closely related / transferable evidence, but not an exact match
   - missing: no meaningful evidence
   Use adjacent generously when there is a reasonable transferable match; do not require exact
   title, tool, or keyword overlap.

3. Score with these rules:
   - Any hard must-have = missing -> cap score at 4.
   - Only adjacent gaps, no missing -> cap score at 7.
   - All hard must-haves direct -> score may be 8-10.
   - Reserve 9-10 for strong overall fit plus direct evidence on all hard must-haves.
   - Apply exclusion rules from the criteria strictly (for example junior roles, pure sales,
     wrong geography, expired postings, or clearly disqualifying missing must-haves).
   - If a job should be excluded, still return it, usually with score 0-2 and a brief reason.

Output fields for each job:
- idx, title, company, location, url
- salary: if mentioned, else null
- short_description: 2-3 sentences
- key_requirements: all notable requirements from the posting
- missing_requirements: every hard must-have that is not direct, annotated as adjacent or missing
  with a short reason
- match_reason: 1-2 sentences that summarize the gap pattern and overall fit
- match_score: integer 0-10

Return ONLY a JSON array of exactly {len(batch)} objects.

--- CANDIDATE PROFILE ---
{profile}

--- JOB SEARCH CRITERIA ---
{criteria}

--- JOBS TO EVALUATE ({len(compact)} items) ---
{json.dumps(compact, ensure_ascii=False)}
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


# --- Batch evaluation ---

def make_batches(shortlisted_jobs: list[dict], batch_size: int = BATCH_SIZE) -> list[list[dict]]:
    return [shortlisted_jobs[i:i + batch_size] for i in range(0, len(shortlisted_jobs), batch_size)]


def _extract_retry_after_seconds(error_message: str) -> float | None:
    """Parse the suggested wait time from an OpenAI rate-limit error message, e.g.
    'Please try again in 6.766s.' Returns None if no explicit hint is found."""
    match = re.search(r"try again in ([\d.]+)s", error_message)
    return float(match.group(1)) if match else None


async def evaluate_batch(
    batch: list[dict],
    profile: str,
    criteria: str,
    batch_num: int,
    total_batches: int,
) -> list[dict]:
    print(f"\n🔍 Batch {batch_num}/{total_batches} — {len(batch)} jobs...")

    evaluator = Agent(
        name="Job Evaluator",
        instructions=build_evaluator_instructions(batch, profile, criteria),
        model=MODEL,
    )

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = await Runner.run(
                evaluator,
                "Evaluate all jobs in this batch now and return the JSON array.",
                max_turns=MAX_TURNS_PER_BATCH,
            )
            break
        except RateLimitError as e:
            last_error = e
            hinted_wait = _extract_retry_after_seconds(str(e))
            wait_seconds = hinted_wait if hinted_wait is not None else RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            print(f"   ⏳ Rate limited (attempt {attempt}/{MAX_RETRIES}) — waiting {wait_seconds:.1f}s before retry...")
            await asyncio.sleep(wait_seconds)
    else:
        raise RuntimeError(
            f"❌ Batch {batch_num} failed after {MAX_RETRIES} rate-limit retries."
        ) from last_error

    batch_results = parse_json_array(result.final_output)

    print(f"   ✅ Got {len(batch_results)}/{len(batch)} results")
    if len(batch_results) < len(batch):
        got_idxs = {r.get("idx") for r in batch_results}
        missing = [j["title"] for j in batch if j["_global_idx"] not in got_idxs]
        print(f"   ⚠️ MISSING: {missing}")

    return batch_results


async def evaluate_all(shortlisted_jobs: list[dict], profile: str, criteria: str) -> list[dict]:
    """Run the Evaluator agent over all shortlisted jobs in batches. Returns combined results.

    No external scraping tool is needed: full_description (captured for every job at Scout
    time from LinkedIn/Indeed's own search APIs) is passed inline in the prompt, so this stage
    is now a pure LLM call with no MCP server dependency."""
    batches = make_batches(shortlisted_jobs)
    print(f"📦 Split {len(shortlisted_jobs)} jobs into {len(batches)} batches of ≤{BATCH_SIZE}")

    all_evaluated: list[dict] = []

    for b_idx, batch in enumerate(batches, 1):
        batch_results = await evaluate_batch(batch, profile, criteria, b_idx, len(batches))
        all_evaluated.extend(batch_results)

        if b_idx < len(batches) and BATCH_DELAY_SECONDS > 0:
            print(f"   ⏸️  Pausing {BATCH_DELAY_SECONDS}s before next batch (rate-limit throttle)...")
            await asyncio.sleep(BATCH_DELAY_SECONDS)

    print(f"\n✅ Total evaluated across all batches: {len(all_evaluated)}/{len(shortlisted_jobs)}")
    return all_evaluated


# --- Ranking ---

def rank_all(evaluated_jobs: list[dict]) -> list[dict]:
    """Sort ALL evaluated jobs by match_score desc (no truncation to top N)."""
    evaluated_jobs.sort(key=lambda j: j.get("match_score", 0), reverse=True)

    print(f"🏆 All {len(evaluated_jobs)} scored jobs (sorted):\n")
    for i, j in enumerate(evaluated_jobs, 1):
        marker = "⭐" if i <= TOP_N else "  "
        print(f"{marker}{i:>3}. [{j['match_score']}/10] {j['title']} @ {j['company']} — {j['location']}")
        print(f"        💬 {j['match_reason']}")
        print(f"        🔗 {j['url']}\n")

    return evaluated_jobs


# --- Orchestration ---

async def run_evaluator(save: bool = True) -> list[dict]:
    """Full evaluator pipeline: load shortlist, evaluate in batches, rank ALL jobs by
    score, optionally save. All scored jobs are written to jobs_ranked.json (not just
    the top N) so lower-scored jobs remain visible for review — TOP_N is used only to
    mark the top slice in the console log, not to filter what gets persisted."""
    shortlisted_jobs = load_shortlisted_jobs()
    profile, criteria = load_profile_and_criteria()

    all_evaluated = await evaluate_all(shortlisted_jobs, profile, criteria)
    ranked = rank_all(all_evaluated)

    if save:
        save_ranked_jobs(ranked)
        print(f"💾 Saved all {len(ranked)} scored jobs → {RANKED_PATH}")

    return ranked


def main():
    import asyncio
    asyncio.run(run_evaluator())


if __name__ == "__main__":
    main()
