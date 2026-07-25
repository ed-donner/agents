from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from asket_mcp import __version__
from asket_mcp.config import get_settings
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

COMMON_TIMEZONES: tuple[str, ...] = (
    "UTC",
    "Europe/London",
    "Europe/Paris",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Asia/Tokyo",
    "Australia/Sydney",
)


def _err(e: Exception) -> str:
    return f"Error: {e}"


def ui_brain_read(path: str) -> str:
    try:
        return brain_read_text(path.strip() or ".")
    except Exception as e:
        return _err(e)


def ui_brain_write(path: str, content: str, overwrite: bool) -> str:
    try:
        rel = brain_write_markdown_impl(path.strip(), content, overwrite=overwrite)
        return f"OK — wrote: {rel}"
    except FileExistsError as e:
        return str(e)
    except Exception as e:
        return _err(e)


def ui_brain_list(dir_path: str) -> str:
    try:
        return brain_list_directory(dir_path.strip() or ".")
    except Exception as e:
        return _err(e)


def ui_brain_find(under: str, glob: str) -> str:
    try:
        return brain_find_files(under.strip() or ".", file_glob=glob.strip() or "*.md")
    except Exception as e:
        return _err(e)


def ui_brain_search(query: str, under: str) -> str:
    try:
        return brain_search_markdown(query.strip(), under_subpath=under.strip() or ".")
    except Exception as e:
        return _err(e)


def ui_brain_delete(path: str, confirmed: bool) -> str:
    try:
        return brain_delete_file_impl(path.strip(), user_confirmed_deletion=confirmed)
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return _err(e)


def ui_fetch(url: str) -> str:
    try:
        return fetch_url_text(url.strip())
    except Exception as e:
        return _err(e)


def ui_note_create(title: str, body: str) -> str:
    try:
        n = get_notes_store().create(title, body)
        return f"Created note #{n.id}: {n.title}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return _err(e)


def ui_note_list() -> str:
    rows = get_notes_store().list_notes(50)
    if not rows:
        return "No scratch notes yet."
    lines = ["id | created_at | title", "--- | --- | ---"]
    for n in rows:
        title = n.title.replace("|", "\\|")
        lines.append(f"{n.id} | {n.created_at} | {title}")
    return "\n".join(lines)


def ui_note_read(note_id: str) -> str:
    try:
        nid = int(note_id.strip())
    except ValueError:
        return "Please type the note number from the list (numbers only, e.g. 3)."
    n = get_notes_store().get(nid)
    if not n:
        return f"No note #{nid}."
    return f"{n.title}\n---\n{n.body}\n---\n{n.created_at}"


def ui_note_delete(note_id: str, confirmed: bool) -> str:
    if not confirmed:
        return "Tick “Yes, delete this note” only when you really want to remove it."
    try:
        nid = int(note_id.strip())
    except ValueError:
        return "Please type the note number from the list (numbers only)."
    ok = get_notes_store().delete(nid)
    return "Deleted." if ok else f"No note #{nid}."


def ui_push(msg: str) -> str:
    try:
        return send_message(msg)
    except PushoverConfigError as e:
        return f"Not configured: {e}"
    except PushoverRequestError as e:
        return _err(e)


def ui_now(tz: str) -> str:
    choice = (tz or "UTC").strip() or "UTC"
    try:
        z = ZoneInfo(choice)
    except ZoneInfoNotFoundError:
        return f"Unknown timezone: {choice!r}"
    return datetime.now(z).isoformat()


def ui_about() -> str:
    s = get_settings()
    key_set = "yes" if (s.openai_api_key or "").strip() else "no"
    sem = ""
    try:
        from asket_mcp.services.vector_brain import collection_count

        sem = f"Semantic index entries: {collection_count()}\n"
    except Exception as e:
        sem = f"Semantic memory: unavailable ({e})\n"
    return (
        f"asket-mcp {__version__}\n"
        f"Brain folder: {brain_root()}\n"
        f"Data / SQLite: {s.data_dir.resolve()}\n"
        f"ChromaDB: {s.chroma_dir()}\n"
        f"{sem}"
        f"OPENAI_API_KEY set: {key_set}\n"
        f"Models — chat: {s.chat_model} | embeddings: {s.embedding_model}\n"
        f"MCP transport (CLI server): {s.mcp_transport}\n"
    )


def ui_semantic_ingest(text: str, label: str) -> str:
    try:
        from asket_mcp.services.vector_brain import ingest_text_chunks

        return ingest_text_chunks(
            text,
            source_id=(label or "ui").strip() or "ui-ingest",
            extra_metadata={"kind": "streamlit_ui"},
        )
    except Exception as e:
        return _err(e)


def ui_semantic_search(query: str) -> str:
    try:
        from asket_mcp.services.vector_brain import format_search_results, semantic_search

        return format_search_results(semantic_search(query))
    except Exception as e:
        return _err(e)


def ui_semantic_ask(question: str) -> str:
    try:
        from asket_mcp.services.agent_logic import ask_the_brain as rag_answer
        from asket_mcp.services.vector_brain import format_search_results, semantic_search

        rows = semantic_search(question)
        ctx = format_search_results(rows)
        return rag_answer(question, ctx)
    except Exception as e:
        return _err(e)


def extract_upload_plain_text(path: Path) -> tuple[str, str]:
    suf = path.suffix.lower()
    try:
        if suf in (".txt", ".md", ".markdown"):
            raw = path.read_text(encoding="utf-8", errors="replace")
            return raw, ""
        if suf == ".csv":
            rows_out: list[str] = []
            with path.open(encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i >= 8000:
                        rows_out.append("… _(CSV truncated after 8000 rows)_")
                        break
                    rows_out.append(" | ".join((c or "").strip() for c in row))
            return "\n".join(rows_out), ""
        if suf == ".pdf":
            try:
                from pypdf import PdfReader
            except ImportError:
                return (
                    "",
                    "PDF text extraction needs **pypdf**. Run: `uv sync --extra ui`",
                )
            reader = PdfReader(str(path))
            parts: list[str] = []
            for i, page in enumerate(reader.pages):
                if i >= 200:
                    parts.append("… _(PDF truncated after 200 pages)_")
                    break
                t = page.extract_text() or ""
                parts.append(t)
            text = "\n\n".join(parts).strip()
            if not text:
                return "", "No extractable text in this PDF (may be scanned images)."
            return text, ""
        if suf == ".docx":
            try:
                from docx import Document
            except ImportError:
                return (
                    "",
                    "Word support needs **python-docx**. Run: `uv sync --extra ui`",
                )
            doc = Document(str(path))
            text = "\n".join(p.text for p in doc.paragraphs if (p.text or "").strip())
            if not text:
                return "", "No paragraph text found in this .docx."
            return text, ""
        return "", f"Unsupported file type `{suf or '(none)'}`."
    except OSError as e:
        return "", str(e)
    except Exception as e:
        return "", _err(e)


def study_partner_reply(message: str, file_path: str | None) -> str:
    msg = (message or "").strip()
    extra_file = ""
    if file_path:
        p = Path(str(file_path).strip())
        if p.is_file():
            raw, err = extract_upload_plain_text(p)
            if err:
                extra_file = f"\n\n_{err}_"
            elif raw:
                cap = 12000
                snippet = raw[:cap] + ("…" if len(raw) > cap else "")
                extra_file = (
                    f"\n\n---\n**From file** `{p.name}` ({len(raw)} chars extracted):\n\n{snippet}"
                )
            else:
                extra_file = f"\n\n_(Empty content from `{p.name}`.)_"
    combined = (msg + extra_file).strip()
    if not combined:
        return (
            "Paste a **URL**, ask a **question**, or attach "
            "**.txt, .md, .csv, .pdf, or .docx** — then **Send**."
        )

    url_m = re.search(r"https?://[^\s<>]+", combined, re.IGNORECASE)
    if url_m:
        url = url_m.group(0).rstrip(").,;]}>'\"")
        try:
            text = fetch_url_text(url)
            cap = 3500
            body = text[:cap] + (
                "…\n\n_(trimmed — use **Read a web page** in More tools for full text)_"
                if len(text) > cap
                else ""
            )
            return f"**Fetched** `{url}` — {len(text)} characters.\n\n---\n\n{body}"
        except Exception as e:
            return _err(e)

    try:
        from asket_mcp.services.agent_logic import ask_the_brain
        from asket_mcp.services.vector_brain import format_search_results, semantic_search

        q = combined[:12000]
        rows = semantic_search(q)
        ctx = format_search_results(rows)
        return ask_the_brain(q, ctx)
    except Exception as e:
        return _err(e)


def study_partner_turn(
    message: str,
    history: list | None,
    file_path: str | None,
) -> tuple[str, list[dict[str, str]]]:
    reply = study_partner_reply(message, file_path)
    user_visible = (message or "").strip()
    if file_path and Path(str(file_path)).is_file():
        tag = Path(str(file_path)).name
        user_visible = (user_visible + f"\n\n📎 `{tag}`") if user_visible else f"📎 `{tag}`"
    h: list[dict[str, str]] = []
    for item in history or []:
        if isinstance(item, dict) and "role" in item and "content" in item:
            h.append({"role": str(item["role"]), "content": str(item["content"])})
    if user_visible:
        h.append({"role": "user", "content": user_visible})
    h.append({"role": "assistant", "content": reply})
    return "", h


def chat_bootstrap() -> list[dict[str, str]]:
    try:
        from asket_mcp.services.agent_logic import greet_and_assess

        p = get_user_profile_store().get_profile()
        text = greet_and_assess(p.goals, p.expertise_level, p.roadmap_markdown)
    except Exception as e:
        text = (
            "Welcome to **Personal Study Brain** — your local study partner.\n\n"
            "- Paste a **link** or ask a **question** (semantic memory + chat model when `OPENAI_API_KEY` is set).\n"
            "- Open **Learning roadmap** to set goals; use **Scratch notes** for quick captures.\n\n"
            f"_Tip: {e}_"
        )
    return [{"role": "assistant", "content": text}]


def roadmap_markdown() -> str:
    p = get_user_profile_store().get_profile()
    goals = p.goals.strip() or "_(Not set yet — add below.)_"
    lvl = p.expertise_level.strip() or "_(Not set)_"
    road = (p.roadmap_markdown or "").strip() or "_No roadmap notes yet._"
    updated = p.updated_at or "—"
    return (
        "### Your learning roadmap\n\n"
        f"**Goals:** {goals}\n\n"
        f"**Level / expertise:** {lvl}\n\n"
        "---\n\n"
        f"{road}\n\n"
        f"---\n\n_Last profile update: {updated}_"
    )


def roadmap_coach_hint() -> str:
    base = roadmap_markdown()
    try:
        from asket_mcp.services.agent_logic import greet_and_assess

        p = get_user_profile_store().get_profile()
        hint = greet_and_assess(p.goals, p.expertise_level, p.roadmap_markdown)
    except Exception as e:
        return base + f"\n\n---\n\n_Coach check-in unavailable: {e}_"
    return base + "\n\n---\n\n### Coach check-in\n\n" + hint


def profile_save(goals: str, expertise: str, roadmap: str) -> str:
    get_user_profile_store().upsert(
        goals=goals or "",
        expertise_level=expertise or "",
        roadmap_markdown=roadmap or "",
    )
    return roadmap_markdown()


def semantic_knowledge_stats() -> str:
    try:
        from asket_mcp.services.vector_brain import collection_count

        n = collection_count()
        return (
            f"**Semantic index:** **{n}** chunk(s) in local Chroma.\n\n"
            "The interactive graph below is a preview — full graph export coming later."
        )
    except Exception as e:
        return f"**Semantic memory:** unavailable (`uv sync --extra semantic`, `OPENAI_API_KEY`).\n\n_{e}_"


def scratch_note_save(title: str, body: str) -> tuple[str, str]:
    t = (title or "").strip()
    b = (body or "").strip()
    if not t:
        return "Title is required.", note_list_short_md()
    try:
        n = get_notes_store().create(t, b)
        msg = f"Saved note **#{n.id}** — _{n.title}_."
    except Exception as e:
        msg = _err(e)
    return msg, note_list_short_md()


def note_list_short_md(limit: int = 12) -> str:
    rows = get_notes_store().list_notes(limit)
    if not rows:
        return "_No scratch notes yet._"
    lines = ["**Recent scratch notes**  ", ""]
    for n in rows:
        preview = (n.body or "").replace("\n", " ").strip()[:72]
        if len((n.body or "")) > 72:
            preview += "…"
        lines.append(f"- **#{n.id}** · {n.title} — _{preview}_")
    return "\n".join(lines)
