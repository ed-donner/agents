"""Shared filesystem paths for crewai_framework_helper."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.getenv("FRAMEWORK_HELPER_ROOT")
    if env:
        return Path(env)
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "pyproject.toml").exists() and (candidate / "rag").is_dir():
            return candidate
    return Path(__file__).resolve().parent.parent


def upstream_repo_dir() -> Path:
    rel = os.getenv("UPSTREAM_DIR", "upstream/crewai")
    return (project_root() / rel).resolve()


def index_dir() -> Path:
    return Path(os.getenv("RAG_INDEX_DIR", project_root() / ".rag_index"))
