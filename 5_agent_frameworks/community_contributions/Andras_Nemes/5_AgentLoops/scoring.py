"""The Python side of the scoring harness: run it, parse it, word it for the agent.

The harness itself is harness.mjs, a plain Node script with the known-answer
physics checks. This module shells out to it and turns its JSON into two things:
the report text the orchestrator agent reads (with every failing check spelled
out, ready to hand to a builder as a fix task) and the short badge line the hub
page shows. Node is already a requirement of the week (npx runs the MCP servers),
so the harness adds no new dependency.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(site_dir: Path, slugs: list[str]) -> dict | None:
    """Score the site with the Node harness and return its parsed JSON.

    Only the given slugs are scored, so a skipped framework does not drag the
    total down. Returns None if Node is missing or the harness output could not
    be parsed, so the caller can degrade gracefully rather than crash the run.
    """
    node = shutil.which("node")
    if node is None:
        return None
    try:
        proc = subprocess.run(
            [node, str(HERE / "harness.mjs"), str(site_dir), *slugs],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return json.loads(proc.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def format_report(result: dict) -> str:
    """The score report the orchestrator agent reads: the total, then each module
    with its failing checks spelled out so they can go straight into a fix task."""
    lines = [f"Score: {result['percent']}% ({result['passed']}/{result['total']} checks passed)."]
    for module in result["modules"]:
        if module["failures"]:
            lines.append(f"{module['key']}: {module['passed']}/{module['total']} passed. Failing checks:")
            lines.extend(f"  - {failure}" for failure in module["failures"])
        else:
            lines.append(f"{module['key']}: all {module['total']} checks passed.")
    return "\n".join(lines)


def badge(result: dict) -> str:
    """The short score line the hub page shows."""
    return f"{result['passed']}/{result['total']} checks nominal ({result['percent']}%)"
