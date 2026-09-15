"""
app.py — Single entry point for the Job Scout pipeline.

Runs all pipeline stages in sequence:
    1. Scout      (job_search.py)      -> jobs_raw.json
    2. Prefilter  (job_prefilter.py)   -> jobs_shortlisted.json
    3. Evaluator  (job_evaluator.py)   -> jobs_ranked.json
    4. UI         (job_ui.py)          -> review, select, generate cover letters

Usage:
    uv run python app.py                 # run full pipeline, then launch UI
    uv run python app.py --skip-search   # reuse existing jobs_raw.json, skip Scout
    uv run python app.py --ui-only       # skip straight to the UI (jobs_ranked.json must exist)

Each stage's checkpoint file (jobs_raw.json, jobs_shortlisted.json, jobs_ranked.json)
is written to disk as usual, so you can also inspect/re-run individual stages with
their own scripts (uv run python job_search.py, etc.) between app.py runs.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from job_search import run_scout, RAW_JOBS_PATH
from job_prefilter import run_prefilter, SHORTLIST_PATH
from job_evaluator import run_evaluator, RANKED_PATH
from job_ui import build_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Job Scout pipeline end-to-end.")
    parser.add_argument(
        "--skip-search", action="store_true",
        help="Skip the Scout stage and reuse the existing jobs_raw.json.",
    )
    parser.add_argument(
        "--skip-prefilter", action="store_true",
        help="Skip the Prefilter stage and reuse the existing jobs_shortlisted.json.",
    )
    parser.add_argument(
        "--skip-evaluator", action="store_true",
        help="Skip the Evaluator stage and reuse the existing jobs_ranked.json.",
    )
    parser.add_argument(
        "--ui-only", action="store_true",
        help="Skip all pipeline stages and launch the UI directly (jobs_ranked.json must exist).",
    )
    return parser.parse_args()


def _require_checkpoint(path: Path, stage_name: str) -> None:
    if not path.exists():
        sys.exit(
            f"❌ Cannot skip {stage_name}: {path} not found. "
            f"Run without --skip flags at least once first."
        )


async def run_pipeline(args: argparse.Namespace) -> None:
    if args.ui_only:
        _require_checkpoint(RANKED_PATH, "all stages (--ui-only)")
        return

    print("=" * 60)
    print("STAGE 1/3 — Scout")
    print("=" * 60)
    if args.skip_search:
        _require_checkpoint(RAW_JOBS_PATH, "Scout")
        print(f"⏭️  Skipped — reusing {RAW_JOBS_PATH}")
    else:
        await run_scout()

    print("\n" + "=" * 60)
    print("STAGE 2/3 — Prefilter")
    print("=" * 60)
    if args.skip_prefilter:
        _require_checkpoint(SHORTLIST_PATH, "Prefilter")
        print(f"⏭️  Skipped — reusing {SHORTLIST_PATH}")
    else:
        await run_prefilter()

    print("\n" + "=" * 60)
    print("STAGE 3/3 — Evaluator")
    print("=" * 60)
    if args.skip_evaluator:
        _require_checkpoint(RANKED_PATH, "Evaluator")
        print(f"⏭️  Skipped — reusing {RANKED_PATH}")
    else:
        await run_evaluator()

    print("\n✅ Pipeline complete. Launching UI...\n")


def main() -> None:
    args = parse_args()
    asyncio.run(run_pipeline(args))

    demo = build_app()
    demo.launch()


if __name__ == "__main__":
    main()
