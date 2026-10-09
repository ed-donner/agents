import asyncio
import html
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Repo root (…/agents): load before research/other imports so MAILTRAP_* / OPENROUTER_* work from any cwd.
REPO_ROOT_FOR_DOTENV = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT_FOR_DOTENV / ".env", override=True)
load_dotenv(override=True)

import pandas as pd
from openai import AsyncOpenAI

from mailtrap_smtp import (
    mailtrap_config_from_env,
    mailtrap_from_addr,
    mailtrap_http_send_configured,
    send_mailtrap_http_sync,
)

from opportunities_research import (
    MODEL,
    OPENROUTER,
    effective_apply_url,
    is_ats_automation_url,
    valid_recruitment_email,
)

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError:
        pass

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


def silence_http_logging() -> None:
    for logger_name in (
        "httpx",
        "httpcore",
        "httpcore.connection",
        "httpcore.http11",
        "httpcore.http2",
        "urllib3",
        "gradio_client",
        "gradio_client.client",
    ):
        logging.getLogger(logger_name).setLevel(logging.ERROR)


silence_http_logging()

APPLICATIONS_JSON_PATH = Path(__file__).resolve().parent / "applications.json"

LOG_POLL_INTERVAL_SECONDS = 0.12


def read_applications_store() -> dict:
    if not APPLICATIONS_JSON_PATH.exists():
        return {"applications": []}
    try:
        return json.loads(APPLICATIONS_JSON_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"applications": []}


def write_applications_store(data: dict) -> None:
    APPLICATIONS_JSON_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def append_application_record(
    *,
    opportunity_name: str,
    opportunity_url: str,
    applicant_name: str,
    applicant_email: str,
    profile_url: str,
    cover_letter: str,
    automation_channel: str = "none",
    automation_log: str = "",
    status: str = "submitted",
    cover_source: str = "",
    contact_email_to: str = "",
) -> dict:
    store = read_applications_store()
    application_id = str(uuid.uuid4())
    record = {
        "application_id": application_id,
        "opportunity_name": opportunity_name.strip(),
        "opportunity_url": opportunity_url.strip(),
        "applicant_name": applicant_name.strip(),
        "applicant_email": applicant_email.strip(),
        "profile_url": profile_url.strip(),
        "cover_letter": cover_letter.strip(),
        "status": status,
        "automation_channel": automation_channel,
        "automation_log": (automation_log or "").strip(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    cover_src_val = (cover_source or "").strip()
    if cover_src_val:
        record["cover_source"] = cover_src_val
    contact_to = (contact_email_to or "").strip()
    if contact_to:
        record["contact_email_to"] = contact_to
    store["applications"].append(record)
    write_applications_store(store)
    return record


def send_mailtrap_subprocess_sync(
    to_addr: str,
    subject: str,
    body: str,
    from_addr: str,
) -> None:
    """
    Run `python mailtrap_smtp.py <payload.json>` in a blocking subprocess.
    Uses stdlib subprocess (not asyncio.create_subprocess_exec) to avoid Windows
    "fileno" / Bad file descriptor inside Gradio's event loop.
    """
    script = Path(__file__).resolve().parent / "mailtrap_smtp.py"
    if not script.is_file():
        raise FileNotFoundError("mailtrap_smtp.py not found next to opportunities_core.py")
    payload = {
        "to_addr": to_addr,
        "subject": subject,
        "body": body,
        "from_addr": from_addr,
    }
    fd, tmp_path = tempfile.mkstemp(suffix=".json", text=True)
    pop_kw: dict = {}
    if sys.platform == "win32":
        cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if cflags:
            pop_kw["creationflags"] = cflags
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        try:
            r = subprocess.run(
                [sys.executable, str(script), tmp_path],
                cwd=str(script.parent),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=120,
                env=os.environ.copy(),
                **pop_kw,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("mailtrap subprocess timed out after 120s") from None
        if r.returncode != 0:
            err = (r.stderr or b"").decode("utf-8", errors="replace").strip()
            msg = err or f"exit {r.returncode}"
            raise RuntimeError(msg[:500])
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def send_mailtrap_subprocess_async(
    to_addr: str,
    subject: str,
    body: str,
    from_addr: str,
) -> None:
    await asyncio.to_thread(
        send_mailtrap_subprocess_sync, to_addr, subject, body, from_addr
    )


async def deliver_mailtrap_email(
    mailtrap_smtp_config: dict,
    to_addr: str,
    subject: str,
    body: str,
    applicant_email: str,
) -> None:
    del mailtrap_smtp_config  # credentials read from env in child or HTTP path
    from_addr = mailtrap_from_addr(applicant_email)
    # HTTPS API avoids SMTP/socket "fileno" failures on Windows inside Gradio/asyncio.
    if mailtrap_http_send_configured():
        send_mailtrap_http_sync(to_addr, subject, body, from_addr)
        return
    await send_mailtrap_subprocess_async(to_addr, subject, body, from_addr)


def use_ai_for_apply() -> bool:
    """Use OpenRouter for cover + resume when OPENROUTER_API_KEY is set."""
    return bool((os.getenv("OPENROUTER_API_KEY") or "").strip())


def load_applications_from_disk() -> list[dict]:
    return list(read_applications_store().get("applications", []))


def format_url_as_html_cell(url: str) -> str:
    u = (url or "").strip()
    if not u:
        return ""
    esc = html.escape(u)
    return (
        f'<a href="{esc}" target="_blank" rel="noopener noreferrer">{esc}</a>'
    )


def build_opportunity_table_rows(
    opportunities: list[dict], applications: list[dict]
) -> list[dict]:
    status_by_url = {
        (a.get("opportunity_url") or "").strip(): a.get("status", "submitted")
        for a in applications
    }
    rows: list[dict] = []
    for opportunity in opportunities:
        apply_url = effective_apply_url(opportunity)
        if (opportunity.get("contact_email") or "").strip():
            channel = "Email"
        elif is_ats_automation_url(apply_url):
            channel = "ATS"
        else:
            channel = "Careers"
        rows.append(
            {
                "Title": opportunity.get("title", ""),
                "URL": format_url_as_html_cell(str(opportunity.get("url", ""))),
                "Deadline": opportunity.get("deadline", ""),
                "Type": opportunity.get("type", ""),
                "Channel": channel,
                "Status": status_by_url.get(apply_url.strip(), "-"),
            }
        )
    return rows


def opportunities_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    cols = ["Title", "URL", "Deadline", "Type", "Channel", "Status"]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)


def clean_listing_hostname(url: str) -> str:
    try:
        h = urlparse((url or "").strip()).netloc.lower()
    except Exception:
        return ""
    if not h or "@" in h:
        return ""
    h = h.split(":")[0].lstrip(".")
    for pre in (
        "www.",
        "careers.",
        "jobs.",
        "apply.",
        "talent.",
        "work.",
        "recruiting.",
        "www2.",
        "my.",
        "portal.",
    ):
        if h.startswith(pre):
            h = h[len(pre) :]
    return h


def employer_display_name_from_listing(job_url: str, listing_title: str) -> str:
    """Best-effort employer wording from listing URL (no scraping)."""
    host = clean_listing_hostname(job_url)
    lt = (listing_title or "").strip()
    if not host:
        return lt or "the organization for this role"
    if host.endswith(".gov") or host.endswith(".gov.uk"):
        return f"the public-sector employer hiring via {host}"
    parts = host.split(".")
    if len(parts) >= 2 and parts[-1] in (
        "com",
        "org",
        "net",
        "io",
        "co",
        "ai",
        "app",
        "uk",
        "us",
        "eu",
    ):
        slug = parts[-2].replace("-", " ").strip()
        if len(slug) >= 2:
            return slug.title()
    return host


def mailing_address_placeholder_line(job_url: str) -> str:
    u = (job_url or "").strip()
    if u:
        return f"Mailing / office address: as shown on the listing ({u})."
    return "Mailing / office address: see the job listing."


def email_sanitize_kwargs_from_opportunity(
    opportunity: dict, applicant_name: str
) -> dict:
    return {
        "job_url": (
            effective_apply_url(opportunity) or opportunity.get("url") or ""
        ).strip(),
        "listing_title": (opportunity.get("title") or "").strip(),
        "applicant_name": (applicant_name or "").strip(),
    }


def format_automation_log_for_ui(automation_log: str) -> str:
    s = (automation_log or "").strip()
    if s.startswith("skip: no employer email"):
        return "SKIP - no employer email on this row"
    if s.startswith("skip:"):
        return f"SKIP - {s[5:].strip()}"
    if s.startswith("email_sent:"):
        return f"EMAIL SENT - {s.removeprefix('email_sent:').strip()}"
    return f"RESULT - {s}"


def squash_merge_field_key(s: str) -> str:
    """Lowercase, drop punctuation/spacing, for fuzzy merge-field matching."""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s'`’\-_:,/]+", "", s.lower())


def replace_square_bracket_merge_field(
    inner: str,
    *,
    today: str,
    employer: str,
    addr_line: str,
    applicant_name: str,
    title_fill: str,
) -> str:
    """Map [ inner ] text to a filled line; unknown template-like labels become empty."""
    raw = unicodedata.normalize("NFKC", (inner or "").strip())
    nk = squash_merge_field_key(raw)

    if not nk:
        return ""

    if nk in ("date", "today", "todaysdate", "currentdate") or (
        "date" in nk and len(nk) <= 28 and "update" not in nk
    ):
        return today

    if ("hiring" in nk or "hrmanager" in nk or nk.startswith("hr")) and (
        "manager" in nk or "name" in nk or nk.endswith("team")
    ):
        return "Hiring Team"
    if nk in ("hiringmanager", "hiringmanagersname", "hiringmanagername"):
        return "Hiring Team"
    if "recipient" in nk and "name" in nk:
        return "Hiring Team"

    if "company" in nk and "address" in nk:
        return addr_line
    if "company" in nk and "name" in nk:
        return employer
    if "employer" in nk and "name" in nk:
        return employer

    if ("city" in nk and "zip" in nk) or ("state" in nk and "zip" in nk):
        return addr_line

    if nk in ("yourname", "applicantname", "candidatename", "fullname"):
        return applicant_name
    if "your" in nk and "name" in nk and len(nk) <= 24:
        return applicant_name

    if "position" in nk and "title" in nk:
        return title_fill
    if nk in ("jobtitle", "roletitle", "positiontitle"):
        return title_fill

    # Short unknown labels (typical mail-merge garbage)
    if len(raw) <= 120 and re.fullmatch(r"[\w\s'’.,/&\-]+", raw, re.I):
        return ""

    return ""


def sanitize_email_plain_text(
    text: str,
    *,
    job_url: str = "",
    listing_title: str = "",
    applicant_name: str = "",
) -> str:
    """
    Convert markdown and mail-merge fields to plain text. Fills or removes [Date], [Company Name], etc.
    """
    t = (text or "").replace("\r\n", "\n").strip()
    if not t:
        return ""
    t = unicodedata.normalize("NFKC", t)
    t = t.replace("\u00a0", " ").replace("\ufeff", "")
    t = t.replace("\uff3b", "[").replace("\uff3d", "]")
    t = (
        t.replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u02bc", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )
    for zw in (
        "\u200b",
        "\u200c",
        "\u200d",
        "\u2060",
    ):
        t = t.replace(zw, "")

    # Markdown links first (before generic [...] handling)
    t = re.sub(
        r"\[([^\]]+)\]\s*\(\s*(https?://[^\s)]+)\s*\)",
        r"\1: \2",
        t,
        flags=re.I,
    )
    t = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", r"\1: \2", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"\*([^*]+)\*", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)

    today = date.today().strftime("%d %B %Y")
    employer = employer_display_name_from_listing(job_url, listing_title)
    addr_line = mailing_address_placeholder_line(job_url)
    applicant_display_name = (applicant_name or "").strip()
    title_fill = (listing_title or "").strip() or "this role"

    def replace_bracket_placeholder(match: re.Match) -> str:
        return replace_square_bracket_merge_field(
            match.group(1),
            today=today,
            employer=employer,
            addr_line=addr_line,
            applicant_name=applicant_display_name,
            title_fill=title_fill,
        )

    # Repeat: nested or adjacent tokens
    for _pass in range(6):
        t2 = re.sub(r"\[\s*([^\[\]\n]+?)\s*\]", replace_bracket_placeholder, t)
        if t2 == t:
            break
        t = t2

    t = re.sub(r"Dear\s*\[\s*[^\]\n]{1,200}\]\s*,?", "Dear Hiring Team,", t, flags=re.I)
    t = re.sub(r"Dear\s+Hiring\s+Team\s+Hiring\s+Team", "Dear Hiring Team", t, flags=re.I)
    t = re.sub(r"Dear\s*,", "Dear Hiring Team,", t, flags=re.I)
    t = re.sub(r"Dear\s+\.", "Dear Hiring Team.", t, flags=re.I)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,", ",", t)

    out_lines: list[str] = []
    for line in t.split("\n"):
        ln = re.sub(r"[ \t]{2,}", " ", line).strip()
        if not ln:
            out_lines.append("")
            continue
        if re.fullmatch(r"\[[^\]]+\]", ln):
            filled = replace_square_bracket_merge_field(
                ln[1:-1],
                today=today,
                employer=employer,
                addr_line=addr_line,
                applicant_name=applicant_display_name,
                title_fill=title_fill,
            )
            if filled:
                out_lines.append(filled)
            continue
        out_lines.append(ln)
    t = "\n".join(out_lines)
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n[ \t]+", "\n", t)
    return t.strip()


def cover_letter_template(
    opportunity: dict, name: str, email: str, profile: str
) -> str:
    title = (opportunity.get("title") or "the role").strip()
    return (
        f"Dear Hiring Team,\n\n"
        f"I am writing to apply for {title}. "
        f"I would welcome the chance to discuss how my experience fits the role.\n\n"
        f"You can reach me at {email}. "
        f"LinkedIn: {profile}\n\n"
        f"Best regards,\n{name}"
    )


async def generate_cover_letter_llm(
    opportunity: dict, name: str, email: str, profile: str, focus: str
) -> str:
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    client = AsyncOpenAI(base_url=OPENROUTER, api_key=api_key)
    model = os.getenv("OPENROUTER_MODEL") or MODEL
    title = (opportunity.get("title") or "the position").strip()
    focus_context = (
        (focus or "").strip() or "Relevant technical experience and motivation."
    )
    listing_url = (
        effective_apply_url(opportunity) or opportunity.get("url") or ""
    ).strip()
    msg = (
        f"Write the body of a job-application email (what the candidate sends to the employer), not a formal letter "
        f"with mail-merge fields.\n\n"
        f"Job title: {title}\n"
        f"Listing URL: {listing_url or '(unknown)'}\n"
        f"Candidate name: {name}\n"
        f"Email: {email}\n"
        f"LinkedIn URL (plain text only, no markdown): {profile}\n"
        f"Emphasize fit for: {focus_context}\n\n"
        "Strict rules:\n"
        "- Output plain text only. ASCII letters, numbers, and basic punctuation only (no smart quotes or emojis).\n"
        "- No markdown (no **bold**, no [label](url) links). For LinkedIn write: LinkedIn: then the URL on the same line.\n"
        "- Never use square brackets or mail-merge tokens: no [Date], [Employer], [Company Name], [Address], [Zip], "
        "or ANY [text in brackets]. Start with exactly: Dear Hiring Team,\n"
        f"- You may refer to the employer using only neutral wording implied by the listing URL (e.g. .gov = public sector); "
        f"do not invent a street address.\n"
        "- 3-4 short paragraphs: why this role, strengths, remote/availability if relevant, thanks.\n"
        "- End with Sincerely, or Best regards, then a new line with the candidate's real name only.\n"
        "- No letterhead block (no blocks of address lines above the greeting)."
    )
    r = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": msg}],
        temperature=0.45,
        max_tokens=1200,
    )
    text = (r.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("empty completion")
    sanitize_kwargs = email_sanitize_kwargs_from_opportunity(opportunity, name)
    return sanitize_email_plain_text(text, **sanitize_kwargs)[:12000]


async def resolve_cover_letter(
    opportunity: dict,
    name: str,
    email: str,
    profile: str,
    focus: str,
    use_ai: bool,
) -> tuple[str, str]:
    """Returns (cover_text, cover_source: template|ai)."""
    if use_ai:
        try:
            text = await generate_cover_letter_llm(
                opportunity, name, email, profile, focus
            )
            return text, "ai"
        except Exception:
            pass
    sanitize_kwargs = email_sanitize_kwargs_from_opportunity(opportunity, name)
    return (
        sanitize_email_plain_text(
            cover_letter_template(opportunity, name, email, profile),
            **sanitize_kwargs,
        ),
        "template",
    )


def build_email_apply_body(
    opportunity: dict,
    name: str,
    applicant_email: str,
    profile_url: str,
    job_url: str,
    cover: str,
    resume_text: str,
) -> str:
    title = (opportunity.get("title") or "Role").strip()
    sanitize_kwargs = {
        "job_url": (job_url or "").strip(),
        "listing_title": title,
        "applicant_name": (name or "").strip(),
    }
    cover = sanitize_email_plain_text(cover, **sanitize_kwargs)
    resume_clean = sanitize_email_plain_text(
        (resume_text or "").strip(), **sanitize_kwargs
    )
    intro = (
        f"I am applying for: {title}\n"
        f"Listing: {job_url}"
    )
    parts = [intro, "", cover]
    if resume_clean:
        parts += [
            "",
            "---",
            "Professional background (summary)",
            resume_clean,
        ]
    parts += [
        "",
        "---",
        f"{name} | {applicant_email} | {profile_url}",
    ]
    return "\n".join(parts)


async def generate_resume_from_linkedin_context_llm(
    name: str,
    applicant_email: str,
    linkedin_profile_url: str,
    focus: str,
    *,
    job_url: str = "",
    listing_title: str = "",
) -> str:
    """Plain-text resume inferred from the candidate context; we do not scrape LinkedIn."""
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    client = AsyncOpenAI(base_url=OPENROUTER, api_key=api_key)
    model = os.getenv("OPENROUTER_MODEL") or MODEL
    focus_context = (
        (focus or "").strip() or "Software / professional experience"
    )
    linkedin_display = (linkedin_profile_url or "").strip() or "(not provided)"
    listing_url = (job_url or "").strip()
    listing_title_clean = (listing_title or "").strip()
    prompt = (
        f"The candidate's name is {name}, email {applicant_email}. LinkedIn profile URL: {linkedin_display}. "
        f"Target role / listing title: {listing_title_clean or '(not specified)'}. "
        f"Listing URL (context only): {listing_url or '(none)'}. "
        "You cannot browse LinkedIn; write a plausible plain-text resume "
        f"consistent with: {focus_context}. "
        "Max ~350 words. Sections: Summary, Skills, Experience (bullets), Education. "
        "ASCII plain text only: no markdown, no [square brackets] or ANY bracketed placeholders, no **asterisks**, "
        "no emojis. "
        "Do not invent real company names or street addresses; use neutral phrases like 'Confidential client' or "
        "'Remote contract' if needed."
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35,
        max_tokens=1400,
    )
    raw_text = (response.choices[0].message.content or "").strip()
    return sanitize_email_plain_text(
        raw_text,
        job_url=listing_url,
        listing_title=listing_title_clean,
        applicant_name=name.strip(),
    )[:12000]


async def apply_single_opportunity(
    opportunity: dict,
    name: str,
    profile_url: str,
    email: str,
    index: int,
    total: int,
    log: list[str],
    *,
    focus: str = "",
) -> None:
    profile_url = profile_url.strip()
    listing_apply_url = effective_apply_url(opportunity)
    title = (opportunity.get("title") or "Job")[:200]
    apply_mode = (opportunity.get("apply_mode") or "").strip().lower()
    employer_email = (opportunity.get("contact_email") or "").strip()
    use_ai = use_ai_for_apply()
    log.append(f"  [{index}/{total}] {title}")
    log.append(f"      Listing: {listing_apply_url}")
    if apply_mode == "api":
        log.append("      Skipped - apply_mode=api not supported here")
        automation_log = "skip: api apply not supported"
        cover, cover_source = await resolve_cover_letter(
            opportunity, name.strip(), email, profile_url, focus, use_ai
        )
        record = append_application_record(
            opportunity_name=(opportunity.get("title") or "")[:500],
            opportunity_url=listing_apply_url,
            applicant_name=name.strip(),
            applicant_email=email,
            profile_url=profile_url,
            cover_letter=cover,
            automation_channel="none",
            automation_log=automation_log,
            status="skipped",
            cover_source=cover_source,
        )
        log.append(f"      Outcome: {format_automation_log_for_ui(automation_log)}")
        log.append(
            f"      Local record: SAVED - application_id={record['application_id'][:8]}... "
            f"status={record['status']}  channel={record.get('automation_channel', '-')}"
        )
        return

    if not employer_email or not valid_recruitment_email(employer_email):
        log.append(
            "      No employer email - skipped (agent should set contact_email; try extract_emails_from_url)"
        )
        automation_log = "skip: no employer email"
        cover, cover_source = await resolve_cover_letter(
            opportunity, name.strip(), email, profile_url, focus, use_ai
        )
        record = append_application_record(
            opportunity_name=(opportunity.get("title") or "")[:500],
            opportunity_url=listing_apply_url,
            applicant_name=name.strip(),
            applicant_email=email,
            profile_url=profile_url,
            cover_letter=cover,
            automation_channel="none",
            automation_log=automation_log,
            status="skipped_no_email",
            cover_source=cover_source,
        )
        log.append(f"      Outcome: {format_automation_log_for_ui(automation_log)}")
        log.append(
            f"      Local record: SAVED - application_id={record['application_id'][:8]}... "
            f"status={record['status']}  channel={record.get('automation_channel', '-')}"
        )
        return

    log.append(f"      Sending to: {employer_email}")
    cover, cover_source = await resolve_cover_letter(
        opportunity, name.strip(), email, profile_url, focus, use_ai
    )
    if cover_source == "ai":
        log.append("      Cover letter: AI (OpenRouter)")
    resume_text = ""
    if use_ai:
        try:
            resume_text = await generate_resume_from_linkedin_context_llm(
                name.strip(),
                email,
                profile_url,
                focus,
                job_url=listing_apply_url,
                listing_title=(opportunity.get("title") or "").strip(),
            )
            log.append("      Resume: AI from LinkedIn URL context (OpenRouter)")
        except Exception as exc:
            log.append(f"      Resume: omitted ({str(exc)[:80]})")
    body = build_email_apply_body(
        opportunity,
        name.strip(),
        email,
        profile_url,
        listing_apply_url,
        cover,
        resume_text,
    )
    body = sanitize_email_plain_text(
        body,
        job_url=listing_apply_url,
        listing_title=(opportunity.get("title") or "").strip(),
        applicant_name=name.strip(),
    )
    subject = f"Application: {title}"[:200]
    smtp_config = mailtrap_config_from_env()
    http_send_ready = mailtrap_http_send_configured()
    if not smtp_config and not http_send_ready:
        automation_log = (
            "skip: Mailtrap not configured (MAILTRAP_API_KEY + MAILTRAP_INBOX_ID for sandbox HTTP, "
            "or MAILTRAP_USER + MAILTRAP_PASSWORD with host containing 'mailtrap')"
        )
        channel = "none"
    else:
        try:
            await deliver_mailtrap_email(
                smtp_config or {}, employer_email, subject, body, email.strip()
            )
            automation_log = f"email_sent:{employer_email}"
            channel = "email"
        except Exception as exc:
            automation_log = f"skip: email send failed ({str(exc)[:200]})"
            channel = "none"
    log.append(f"      Outcome: {format_automation_log_for_ui(automation_log)}")
    app_status = "submitted" if automation_log.startswith("email_sent:") else "failed"
    record = append_application_record(
        opportunity_name=(opportunity.get("title") or "")[:500],
        opportunity_url=listing_apply_url,
        applicant_name=name.strip(),
        applicant_email=email,
        profile_url=profile_url,
        cover_letter=cover,
        automation_channel=channel,
        automation_log=automation_log,
        status=app_status,
        cover_source=cover_source,
        contact_email_to=employer_email if channel == "email" else "",
    )
    log.append(
        f"      Local record: SAVED - application_id={record['application_id'][:8]}... "
        f"status={record['status']}  channel={record.get('automation_channel', '-')}"
    )
