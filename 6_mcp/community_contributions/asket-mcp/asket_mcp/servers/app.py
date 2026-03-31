from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mcp.server.fastmcp import FastMCP

from asket_mcp import __version__
from asket_mcp.config import get_settings, mcp_log_level, normalized_transport
from asket_mcp.logging_config import configure_logging
from asket_mcp.services.brain_fs import (
    brain_delete_file as brain_delete_file_impl,
    brain_find_files,
    brain_list_directory,
    brain_read_text,
    brain_root,
    brain_search_markdown,
    brain_write_markdown as brain_write_markdown_impl,
)
from asket_mcp.services.pushover import PushoverConfigError, PushoverRequestError, send_message
from asket_mcp.services.url_fetch import fetch_url_text
from asket_mcp.store.notes import get_notes_store
from asket_mcp.store.user_profile import get_user_profile_store

logger = logging.getLogger(__name__)


def _semantic_error(e: BaseException) -> str:
    return f"Semantic / coach error: {e}"

_INSTRUCTIONS = """You are backing a Local-First study workflow with optional semantic memory (ChromaDB locally + OpenAI embeddings/chat when enabled).

**Filesystem Brain** — use **brain_*** tools for Markdown under the configured Brain folder only (no path escape).
**Public web** — **fetch_public_page** for http(s) text (not a full browser).
**Semantic memory** (requires `semantic` extra + `OPENAI_API_KEY`): **semantic_memory_ingest_*** fills local Chroma; **semantic_memory_search** retrieves by meaning; **ask_the_brain** runs RAG. Text you send is POSTed to OpenAI per their service terms.
**Learner profile** — **study_profile_get** / **study_profile_update** for goals, expertise, roadmap; **greet_and_assess** for a short coach welcome using that profile.

Human-in-the-loop defaults:
- **brain_write_markdown**: `overwrite=true` only after the user approves replacing a file.
- **brain_delete_file** and **note_delete**: `user_confirmed_deletion=true` only after explicit approval.

Prefer durable summaries as `.md` in the Brain tree. Use **semantic_memory_ingest_brain_file** after major writes if the user wants RAG coverage. Keyword search: **brain_search_notes**."""

mcp = FastMCP(
    name="personal-study-brain",
    instructions=_INSTRUCTIONS,
    host=get_settings().mcp_host,
    port=get_settings().mcp_port,
    log_level=mcp_log_level(),
)


@mcp.tool()
async def brain_read_file(relative_path: str) -> str:
    """Read a UTF-8 text or Markdown file from the Brain folder (relative path, posix-style)."""
    try:
        return brain_read_text(relative_path)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def brain_write_markdown(relative_path: str, content: str, overwrite: bool = False) -> str:
    """Write Markdown/text into the Brain folder. Set overwrite=true only after the user approves replacing an existing file."""
    try:
        rel = brain_write_markdown_impl(relative_path, content, overwrite=overwrite)
        return f"Wrote Brain file: {rel}"
    except FileExistsError as e:
        return str(e)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def brain_list_files(relative_path: str = ".", max_entries: int = 200) -> str:
    """List files and subdirectories under a path inside the Brain folder."""
    try:
        return brain_list_directory(relative_path, max_entries=max_entries)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def brain_find_markdown_files(under_subpath: str = ".", file_glob: str = "*.md", max_files: int = 200) -> str:
    """Discover Markdown files recursively under a Brain subpath (default: all *.md)."""
    try:
        return brain_find_files(under_subpath, file_glob=file_glob, max_files=max_files)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def brain_search_notes(query: str, under_subpath: str = ".", max_file_hits: int = 30) -> str:
    """Search for a phrase inside .md files under the Brain (case-insensitive); returns paths and snippets."""
    try:
        return brain_search_markdown(query, under_subpath=under_subpath, max_file_hits=max_file_hits)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def brain_delete_file(relative_path: str, user_confirmed_deletion: bool = False) -> str:
    """Delete a file inside the Brain. Requires user_confirmed_deletion=true after explicit human approval."""
    try:
        return brain_delete_file_impl(relative_path, user_confirmed_deletion=user_confirmed_deletion)
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
async def send_push(message: str) -> str:
    """Send a short mobile notification via Pushover (optional; requires credentials)."""
    try:
        return send_message(message)
    except PushoverConfigError as e:
        return f"Not configured: {e}"
    except PushoverRequestError as e:
        return f"Pushover error: {e}"


@mcp.tool()
async def fetch_public_page(url: str) -> str:
    """Fetch a public http(s) page as text for study/source digest (HTML loosely stripped; size capped)."""
    try:
        return fetch_url_text(url)
    except Exception as e:
        logger.info("fetch failed: %s", e)
        return f"Could not fetch URL: {e}"


@mcp.tool()
async def current_time(timezone_name: str = "UTC") -> str:
    """Current time as ISO-8601 in an IANA timezone (e.g. America/New_York)."""
    try:
        tz = ZoneInfo(timezone_name.strip() or "UTC")
    except ZoneInfoNotFoundError:
        return f"Unknown timezone: {timezone_name!r}. Use an IANA name like Europe/Paris."
    return datetime.now(tz).isoformat()


@mcp.tool()
async def note_create(title: str, body: str) -> str:
    """Quick SQLite scratch note (separate from Brain files; for short captures)."""
    try:
        n = get_notes_store().create(title, body)
        return f"Created note #{n.id}: {n.title}"
    except ValueError as e:
        return str(e)


@mcp.tool()
async def note_list(limit: int = 20) -> str:
    """List recent scratch notes (newest first)."""
    rows = get_notes_store().list_notes(int(limit))
    if not rows:
        return "No notes yet."
    lines = [f"{n.id}\t{n.created_at}\t{n.title}" for n in rows]
    return "\n".join(lines)


@mcp.tool()
async def note_read(note_id: int) -> str:
    """Read one scratch note by id."""
    n = get_notes_store().get(int(note_id))
    if not n:
        return f"No note with id {note_id}."
    return f"{n.title}\n---\n{n.body}\n---\n{n.created_at}"


@mcp.tool()
async def note_delete(note_id: int, user_confirmed_deletion: bool = False) -> str:
    """Delete a scratch note. Requires user_confirmed_deletion=true after explicit human approval."""
    if not user_confirmed_deletion:
        return "Blocked: set user_confirmed_deletion=true only after the user explicitly approves deletion."
    ok = get_notes_store().delete(int(note_id))
    return "Deleted." if ok else f"No note with id {note_id}."


@mcp.tool()
async def semantic_memory_ingest_text(text: str, source_label: str, tags: str = "") -> str:
    """Chunk and embed text into local ChromaDB (requires OPENAI_API_KEY + `uv sync --extra semantic`). source_label should be unique and human-readable (e.g. lecture-2025-03)."""
    try:
        from asket_mcp.services.vector_brain import ingest_text_chunks

        label = (source_label or "inline").strip() or "inline"
        meta: dict = {}
        if (tags or "").strip():
            meta["tags"] = tags.strip()[:500]
        return ingest_text_chunks(text, source_id=label, extra_metadata=meta or None)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def semantic_memory_ingest_brain_file(relative_path: str, tags: str = "") -> str:
    """Read a UTF-8 file from the Brain folder and ingest it into semantic memory."""
    try:
        from asket_mcp.services.vector_brain import ingest_text_chunks

        body = brain_read_text(relative_path)
        label = f"brain:{relative_path.strip()}"
        meta: dict = {"kind": "brain_file", "relative_path": relative_path.strip()[:2000]}
        if (tags or "").strip():
            meta["tags"] = tags.strip()[:500]
        return ingest_text_chunks(body, source_id=label, extra_metadata=meta)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def semantic_memory_ingest_url(url: str, source_label: str = "", tags: str = "") -> str:
    """Fetch a public URL as text and ingest into semantic memory."""
    try:
        from asket_mcp.services.vector_brain import ingest_text_chunks

        page = fetch_url_text(url)
        label = (source_label or "").strip() or f"url:{url.strip()[:180]}"
        meta: dict = {"kind": "url", "url": url.strip()[:2000]}
        if (tags or "").strip():
            meta["tags"] = tags.strip()[:500]
        return ingest_text_chunks(page, source_id=label, extra_metadata=meta)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def semantic_memory_search(query: str, top_k: int = 8) -> str:
    """Semantic (vector) search over ingested passages; returns snippets and source metadata."""
    try:
        from asket_mcp.services.vector_brain import format_search_results, semantic_search

        rows = semantic_search(query, top_k=int(top_k))
        return format_search_results(rows)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def ask_the_brain(question: str) -> str:
    """Answer a study question using local semantic retrieval + OpenAI chat (RAG)."""
    try:
        from asket_mcp.services.agent_logic import ask_the_brain as rag_answer
        from asket_mcp.services.vector_brain import format_search_results, semantic_search

        rows = semantic_search(question)
        ctx = format_search_results(rows)
        return rag_answer(question, ctx)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def study_profile_get() -> str:
    """Return saved learner goals, expertise level, and roadmap notes."""
    p = get_user_profile_store().get_profile()
    return (
        f"goals: {p.goals or '(empty)'}\n"
        f"expertise_level: {p.expertise_level or '(empty)'}\n"
        f"roadmap_markdown:\n{p.roadmap_markdown or '(empty)'}\n"
        f"updated_at: {p.updated_at}"
    )


@mcp.tool()
async def study_profile_update(
    goals: str | None = None,
    expertise_level: str | None = None,
    roadmap_markdown: str | None = None,
) -> str:
    """Update learner profile fields. Omit a parameter to leave it unchanged."""
    if goals is None and expertise_level is None and roadmap_markdown is None:
        return (
            "No changes (pass at least one of goals, expertise_level, roadmap_markdown).\n"
            + (await study_profile_get())
        )
    try:
        p = get_user_profile_store().upsert(
            goals=goals,
            expertise_level=expertise_level,
            roadmap_markdown=roadmap_markdown,
        )
        return (
            "Updated study profile.\n"
            f"goals: {p.goals or '(empty)'}\n"
            f"expertise_level: {p.expertise_level or '(empty)'}\n"
            f"roadmap_markdown:\n{p.roadmap_markdown or '(empty)'}\n"
            f"updated_at: {p.updated_at}"
        )
    except Exception as e:
        return f"Profile error: {e}"


@mcp.tool()
async def greet_and_assess() -> str:
    """Short welcoming message and next-step hints based on study_profile (uses OpenAI)."""
    try:
        from asket_mcp.services.agent_logic import greet_and_assess as greet

        p = get_user_profile_store().get_profile()
        return greet(p.goals, p.expertise_level, p.roadmap_markdown)
    except Exception as e:
        return _semantic_error(e)


@mcp.tool()
async def asket_info() -> str:
    """Server version and resolved Brain root (sanity check)."""
    root = brain_root()
    s = get_settings()
    sem = ""
    try:
        from asket_mcp.services.vector_brain import collection_count

        sem = f" | semantic_index_size={collection_count()}"
    except Exception:
        sem = " | semantic_index=unavailable"
    return (
        f"asket-mcp {__version__} | Brain: {root} | transport: {s.mcp_transport}"
        f"{sem}"
    )


@mcp.resource("notes://recent")
async def notes_recent_resource() -> str:
    """Recent SQLite scratch notes (not the Brain tree)."""
    rows = get_notes_store().list_notes(20)
    if not rows:
        return "No notes."
    parts: list[str] = []
    for n in rows:
        preview = (n.body[:200] + "…") if len(n.body) > 200 else n.body
        parts.append(f"#{n.id} {n.created_at} {n.title}\n{preview}\n")
    return "\n".join(parts)


@mcp.resource("brain://root")
async def brain_root_resource() -> str:
    """Absolute path of the allow-listed Brain directory."""
    return str(brain_root())


def main() -> None:
    configure_logging()
    settings = get_settings()
    transport = normalized_transport()
    logger.info("Starting asket-mcp %s transport=%s brain=%s", __version__, transport, brain_root())
    if transport != "stdio" and settings.mcp_host in ("0.0.0.0", "::", "[::]"):
        logger.warning(
            "MCP listens on all interfaces (%s) over %s. Use a firewall, TLS termination, "
            "or bind to 127.0.0.1 if clients connect through a local reverse proxy.",
            settings.mcp_host,
            transport,
        )
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
