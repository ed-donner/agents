"""
Kirundi Study Brain MCP server (FastMCP, stdio).

Local-first Markdown corpus + learner profile + grounded tutoring tools.
"""

from __future__ import annotations

import json
import logging

from mcp.server.fastmcp import FastMCP

from kirundi_brain import __version__, brain_fs, config
from kirundi_brain.profile_store import ProfileStore
from kirundi_brain.tutor import ask_kirundi, grade_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kirundi_brain")

_INSTRUCTIONS = """You back a Kirundi (Rundi) study workflow for Burundi.

Use brain_* tools for Markdown under the Brain folder only (path jail).
Use profile_* to personalize coaching.
Use ask_kirundi for grounded Q&A (retrieve corpus, then explain).
Use grade_kirundi_answer after short speaking/writing drills.

Human-in-the-loop:
- brain_write_markdown: overwrite=true only after learner approval.
- brain_delete_file: user_confirmed_deletion=true only after explicit approval.
Prefer durable lessons as .md in the Brain. Do not invent vocabulary outside tools.
"""

mcp = FastMCP(name="kirundi-study-brain", instructions=_INSTRUCTIONS)


def _profile() -> ProfileStore:
    return ProfileStore(config.data_dir() / "learner_profile.sqlite3")


@mcp.tool()
async def brain_list_files(relative_path: str = ".") -> str:
    """List files and folders inside the Kirundi Brain corpus."""
    return brain_fs.list_directory(config.brain_root(), relative_path)


@mcp.tool()
async def brain_read_file(relative_path: str) -> str:
    """Read a Markdown/text lesson from the Kirundi Brain (relative path)."""
    return brain_fs.read_text(config.brain_root(), relative_path)


@mcp.tool()
async def brain_search_notes(query: str, under_subpath: str = ".") -> str:
    """Keyword-search .md lessons (case-insensitive) and return path + snippets."""
    return brain_fs.search_markdown(config.brain_root(), query, under_subpath=under_subpath)


@mcp.tool()
async def brain_write_markdown(
    relative_path: str,
    content: str,
    overwrite: bool = False,
) -> str:
    """Write a lesson into the Brain. Set overwrite=true only after learner approval."""
    return brain_fs.write_markdown(
        config.brain_root(),
        relative_path,
        content,
        overwrite=overwrite,
    )


@mcp.tool()
async def brain_delete_file(
    relative_path: str,
    user_confirmed_deletion: bool = False,
) -> str:
    """Delete a Brain file. Set user_confirmed_deletion=true only after explicit approval."""
    return brain_fs.delete_file(
        config.brain_root(),
        relative_path,
        confirmed=user_confirmed_deletion,
    )


@mcp.tool()
async def profile_get() -> str:
    """Return the learner profile (level, goals, recent mistakes)."""
    return json.dumps(_profile().get(), ensure_ascii=False, indent=2)


@mcp.tool()
async def profile_update(
    display_name: str | None = None,
    level: str | None = None,
    goals_json: str | None = None,
    recent_mistakes_json: str | None = None,
    notes: str | None = None,
) -> str:
    """Update learner profile fields. goals_json / recent_mistakes_json are JSON string arrays."""
    goals = json.loads(goals_json) if goals_json else None
    mistakes = json.loads(recent_mistakes_json) if recent_mistakes_json else None
    if goals is not None and not isinstance(goals, list):
        return "Error: goals_json must be a JSON array of strings."
    if mistakes is not None and not isinstance(mistakes, list):
        return "Error: recent_mistakes_json must be a JSON array of strings."
    updated = _profile().update(
        display_name=display_name,
        level=level,
        goals=goals,
        recent_mistakes=mistakes,
        notes=notes,
    )
    return json.dumps(updated, ensure_ascii=False, indent=2)


@mcp.tool()
async def ask_kirundi_tutor(question: str) -> str:
    """Answer a Kirundi question using Brain retrieval + optional OpenAI grounding."""
    level = _profile().get().get("level", "A1")
    return ask_kirundi(config.brain_root(), question, learner_level=str(level))


@mcp.tool()
async def grade_kirundi_answer(
    prompt_en: str,
    learner_reply: str,
    expected_hint: str = "",
) -> str:
    """Grade a short Kirundi reply; returns score, correction, and feedback."""
    return grade_answer(
        config.brain_root(),
        prompt_en=prompt_en,
        learner_reply=learner_reply,
        expected_hint=expected_hint,
    )


@mcp.tool()
async def kirundi_brain_info() -> str:
    """Return server version, Brain path, and data directory."""
    info = {
        "name": "kirundi-study-brain",
        "version": __version__,
        "brain_dir": str(config.brain_root()),
        "data_dir": str(config.data_dir()),
        "model": config.openai_model(),
        "openai_configured": bool(config.openai_api_key()),
    }
    return json.dumps(info, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
