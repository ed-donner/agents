"""The agent loop: a Google ADK orchestrator agent that runs the whole Week 5 team.

The orchestrator is itself an agent. Given the workers you built across the week and
a language to teach, it authors a shared look, hands each framework's worker a game
to build, launches them in parallel against one shared board, watches that board fill
in live, then plays each finished game in a real browser to check it and sends a
builder back to fix any that do not work. Open the printed index.html to play.

    uv run agent_loop.py                    # a Spanish arcade from every worker you have
    uv run agent_loop.py --language French   # any language
    uv run agent_loop.py --skip agno         # leave a framework out
    uv run agent_loop.py --dry-run           # show the plan without running the agent
    uv run agent_loop.py --no-open           # build it but do not open the browser at the end
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a language-game arcade with the Week 5 team.")
    parser.add_argument("--language", default="Spanish", help="the language to learn (default: Spanish)")
    parser.add_argument("--skip", nargs="*", default=[], help="worker keys to leave out, e.g. --skip agno mastra")
    parser.add_argument("--dry-run", action="store_true", help="show the plan; do not run the agent")
    parser.add_argument("--no-open", action="store_true", help="do not open the finished site in a browser")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workers = catalog.discover(skip=tuple(args.skip))
    if not workers:
        raise SystemExit("No worker files found. Build at least one framework's worker first.")

    print(f"Assembling a {args.language} arcade with {len(workers)} builders:")
    for worker in workers:
        print(f"  {worker['name']:<28} -> folder {worker['slug']}/ (game invented at runtime)")
    if args.dry_run:
        print("\nDry run: stopping before the agent runs.")
        return

    print(f"\n{config.ORCHESTRATOR_MODEL} is leading the team. Watch the board fill in:\n")
    orchestrator.run(args.language, workers, SITE, BOARD_PATH)

    # A final deterministic check, so a game the agent missed is still surfaced.
    print("\nFinal check:")
    for worker in workers:
        slug = worker["slug"]
        built = orchestrator.is_built(SITE / slug)
        print(f"  {worker['name']:<28} {'ok' if built else 'INCOMPLETE'}  ({slug}/)")

    index = SITE / "index.html"
    print("\nThe team has finished. Open this to play:")
    print(f"  {index.resolve().as_uri()}")
    if not args.no_open:
        qa_agent.open_site(index)


if __name__ == "__main__":
    main()
