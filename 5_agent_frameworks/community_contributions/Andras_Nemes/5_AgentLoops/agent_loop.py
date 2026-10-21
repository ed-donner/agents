"""Mission Control: a Google ADK orchestrator agent that runs the Week 5 team.

The capstone exercise, on a different problem: instead of an arcade of language
games, the team builds a website of space travel calculators, and a deterministic
physics harness scores the math. The orchestrator launches one builder per
framework against a shared board, measures the site with the harness, and keeps
sending builders back with the failing checks until the score clears the target
or the fix rounds run out. Open the printed index.html to try the calculators.

    uv run agent_loop.py                # build and score the full site
    uv run agent_loop.py --skip agno    # leave a framework out
    uv run agent_loop.py --dry-run      # show the plan without running the agent
    uv run agent_loop.py --no-open      # build it but do not open the browser at the end
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# The orchestrator prints the agents' own words, which can include characters beyond
# the Windows console's default code page (an emoji in a summary, for instance). Make
# stdout UTF-8 so that text renders rather than crashing the run on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv(override=True)  # the orchestrator and its sub-agents make ADK calls, so they need the API keys
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")  # use the Gemini API, not Vertex, as on Day 1

import config  # noqa: E402  # imported after load_dotenv so it sees any model ids set in .env

HERE = Path(__file__).resolve().parent
SITE = HERE / "site"
BOARD_PATH = SITE / "board.sqlite"

# Point both the board and the workers at the shared site before board is imported,
# so every process in the run reads the one shared file and the workers use the chosen
# model. The workers inherit this environment when launched.
os.environ["BOARD_PATH"] = str(BOARD_PATH)
os.environ["WORKER_MODEL"] = config.WORKER_MODEL

import catalog  # noqa: E402
import orchestrator  # noqa: E402
import qa_agent  # noqa: E402
import scoring  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a scored site of space travel calculators with the Week 5 team.")
    parser.add_argument("--skip", nargs="*", default=[], help="worker keys to leave out, e.g. --skip agno mastra")
    parser.add_argument("--dry-run", action="store_true", help="show the plan; do not run the agent")
    parser.add_argument("--no-open", action="store_true", help="do not open the finished site in a browser")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workers = catalog.discover(skip=tuple(args.skip))
    if not workers:
        raise SystemExit("No worker files found. Build at least one framework's worker first.")

    import prompts  # after the env is set, like the other local imports

    print(f"Assembling Mission Control with {len(workers)} builders:")
    for worker in workers:
        print(f"  {worker['name']:<28} -> {prompts.CALC_SPECS[worker['slug']]['short']:<18} (folder {worker['slug']}/)")
    if args.dry_run:
        print("\nDry run: stopping before the agent runs.")
        return

    print(f"\n{config.ORCHESTRATOR_MODEL} is leading the team. Watch the board fill in:\n")
    orchestrator.run(workers, SITE, BOARD_PATH)

    # A final deterministic check, so a page the agent missed is still surfaced.
    print("\nFinal check:")
    for worker in workers:
        slug = worker["slug"]
        built = orchestrator.is_built(SITE / slug)
        print(f"  {worker['name']:<28} {'ok' if built else 'INCOMPLETE'}  ({slug}/)")

    # The measurable outcome: one last harness run, straight from disk, no agent involved.
    result = scoring.run(SITE, [w["slug"] for w in workers])
    if result is not None:
        print(f"\nFinal score: {result['passed']}/{result['total']} checks nominal ({result['percent']}%).")

    index = SITE / "index.html"
    print("\nThe team has finished. Open this to try the calculators:")
    print(f"  {index.resolve().as_uri()}")
    if not args.no_open:
        qa_agent.open_site(index)


if __name__ == "__main__":
    main()
