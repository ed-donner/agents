import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json

from product_factory.flow import DEFAULT_REQUIREMENTS, run_flow


def run(
    workstream_id: str = "main",
    requirements: str = DEFAULT_REQUIREMENTS,
    feedback: str = "",
    reset: bool = True,
) -> None:
    # crewai run should start from a clean sandbox. Aborted runs leave probes and
    # half-written modules that make agents re-read and thrash.
    reset = reset and not feedback.strip()
    result = run_flow(workstream_id, requirements, feedback, reset)
    print(json.dumps(result, indent=2))


def cli() -> None:
    parser = argparse.ArgumentParser(description="Build a product in a sandboxed workstream.")
    parser.add_argument("--workstream-id", default="main")
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--feedback", default="")
    parser.add_argument(
        "--reset",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Wipe and recreate the sandbox before building; skipped for non-empty "
            "feedback so the build can continue (default: on)."
        ),
    )
    args = parser.parse_args()
    run(args.workstream_id, args.requirements, args.feedback, args.reset)


if __name__ == "__main__":
    cli()
