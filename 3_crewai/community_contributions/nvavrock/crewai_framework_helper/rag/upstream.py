"""Clone and sync the upstream crewAIInc/crewAI repository."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from rag.index import load_env
from rag.paths import project_root, upstream_repo_dir

DEFAULT_REPO_URL = "https://github.com/crewAIInc/crewAI"
DEFAULT_REF = "main"


def upstream_dir() -> Path:
    load_env()
    return upstream_repo_dir()


def upstream_url() -> str:
    import os

    load_env()
    return os.getenv("UPSTREAM_REPO_URL", DEFAULT_REPO_URL)


def upstream_ref() -> str:
    import os

    load_env()
    return os.getenv("UPSTREAM_REF", DEFAULT_REF)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _resolve_ref(url: str, ref: str) -> str:
    if ref in ("main", "master"):
        return ref
    result = subprocess.run(
        ["git", "ls-remote", "--tags", url, ref, f"refs/tags/{ref}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip():
        return ref
    print(f"Tag/ref '{ref}' not found on remote; falling back to 'main'.")
    return "main"


def current_commit(repo: Path) -> str | None:
    if not (repo / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or None


def sync_upstream(force_ref: str | None = None) -> Path:
    load_env()
    url = upstream_url()
    dest = upstream_dir()
    ref = force_ref or upstream_ref()
    resolved_ref = _resolve_ref(url, ref)

    dest.parent.mkdir(parents=True, exist_ok=True)

    if not (dest / ".git").exists():
        print(f"Cloning {url} (ref={resolved_ref}) -> {dest}")
        _run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                resolved_ref,
                url,
                str(dest),
            ]
        )
    else:
        print(f"Updating {dest} (ref={resolved_ref})")
        _run(["git", "fetch", "origin", resolved_ref, "--depth", "1"], cwd=dest)
        _run(["git", "checkout", resolved_ref], cwd=dest)
        _run(["git", "reset", "--hard", f"origin/{resolved_ref}"], cwd=dest)

    commit = current_commit(dest)
    if commit:
        print(f"Upstream at {commit[:12]} ({resolved_ref})")
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Clone or update upstream crewAI repo")
    parser.add_argument(
        "--ref",
        help="Git ref to checkout (default: UPSTREAM_REF env or main)",
    )
    args = parser.parse_args()
    path = sync_upstream(force_ref=args.ref)
    print(f"Ready: {path}")


if __name__ == "__main__":
    main()
