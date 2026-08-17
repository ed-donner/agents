"""Shared helpers for munger_analyst inputs and memo filenames.

Memo naming convention (stable for all evaluations):
  output/YYYYMMDD_<company_slug>_memo.md
Example:
  output/20260816_google_memo.md
"""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path


def company_slug(company: str) -> str:
    """Normalize a company/ticker into a safe filename slug."""
    slug = company.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "company"


def date_compact(when: date | datetime | str | None = None) -> str:
    """Return YYYYMMDD for filenames."""
    if when is None:
        when = date.today()
    if isinstance(when, datetime):
        when = when.date()
    if isinstance(when, date):
        return when.strftime("%Y%m%d")
    # Accept "2026-08-16" or "20260816"
    digits = re.sub(r"\D", "", str(when))
    return (digits[:8] if len(digits) >= 8 else date.today().strftime("%Y%m%d"))


def memo_filename(company: str, when: date | datetime | str | None = None) -> str:
    """e.g. 20260816_google_memo.md"""
    return f"{date_compact(when)}_{company_slug(company)}_memo.md"


def memo_path(company: str, when: date | datetime | str | None = None) -> str:
    """e.g. output/20260816_google_memo.md"""
    return f"output/{memo_filename(company, when)}"


def build_inputs(company: str, when: date | None = None) -> dict[str, str]:
    """Inputs for crew kickoff, including interpolated memo_path."""
    day = when or date.today()
    return {
        "company": company.strip(),
        "current_date": str(day),
        "company_slug": company_slug(company),
        "date_compact": date_compact(day),
        "memo_path": memo_path(company, day),
    }


def output_dir() -> Path:
    """Project output/ directory (cwd when running via crewai/uv)."""
    return Path("output")


def list_saved_memos() -> list[Path]:
    """All memo files in output/, newest first."""
    folder = output_dir()
    if not folder.is_dir():
        return []
    memos = sorted(folder.glob("*_memo.md"), reverse=True)
    return memos


def find_latest_memo(company: str) -> Path | None:
    """Find newest output/YYYYMMDD_<slug>_memo.md matching company (or ticker alias)."""
    slug = company_slug(company)
    # Common ticker → slug aliases used in filenames
    aliases = {
        "gis": "general_mills",
        "googl": "google",
        "goog": "google",
        "cvx": "chevron",
        "vz": "verizon",
    }
    targets = {slug, aliases.get(slug, slug)}

    candidates: list[Path] = []
    for path in list_saved_memos():
        # 20260816_general_mills_memo.md → general_mills
        name = path.stem  # 20260816_general_mills_memo
        if not name.endswith("_memo"):
            continue
        body = name[: -len("_memo")]  # 20260816_general_mills
        parts = body.split("_", 1)
        file_slug = parts[1] if len(parts) == 2 else body
        if file_slug in targets or slug in file_slug or file_slug in slug:
            candidates.append(path)
    return candidates[0] if candidates else None


def load_memo_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")
