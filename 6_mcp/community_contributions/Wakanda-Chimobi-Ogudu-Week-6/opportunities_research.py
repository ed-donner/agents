import asyncio
import json
import logging
import os
import re
from datetime import date, timedelta
from urllib.parse import urlparse

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")


def silence_research_http_logging() -> None:
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


import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_community.utilities import GoogleSerperAPIWrapper
from openai import AsyncOpenAI

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, trace

load_dotenv(override=True)
silence_research_http_logging()

OPENROUTER = "https://openrouter.ai/api/v1"
MODEL = os.getenv("OPENROUTER_MODEL") or "openai/gpt-4o-mini"
SERPER_K = 5
PAGE_CHARS = 1800
HTTP_TIMEOUT = 30.0
WINDOW_DAYS = 30
MAX_RESEARCH = 36

FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

BLOCKED_LISTING_HOST_PATTERNS: tuple[str, ...] = (
    "linkedin.com",
    "indeed.com",
    "glassdoor.",
    "ziprecruiter.",
    "monster.com",
    "simplyhired.",
    "careerbuilder.",
    "talent.com",
    "snagajob.",
)
ATS_AUTOMATION_HOST_PATTERNS: tuple[str, ...] = (
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "workable.com",
    "myworkdayjobs.com",
    "smartrecruiters.com",
    "icims.com",
    "bamboohr.com",
)


def normalize_job_host(url: str) -> str:
    try:
        p = urlparse(url.strip())
        if not p.netloc:
            return ""
        return p.netloc.lower().split(":")[0].lstrip("www.")
    except Exception:
        return ""


def host_matches_patterns(host: str, patterns: tuple[str, ...]) -> bool:
    h = host.lower().lstrip("www.")
    for pat in patterns:
        if pat.endswith("."):
            if pat in h:
                return True
        elif h == pat or h.endswith("." + pat):
            return True
    return False


def is_blocked_listing_url(url: str) -> bool:
    host = normalize_job_host(url)
    if not host:
        return True
    return host_matches_patterns(host, BLOCKED_LISTING_HOST_PATTERNS)


def is_ats_automation_url(url: str) -> bool:
    host = normalize_job_host(url)
    if not host:
        return False
    return host_matches_patterns(host, ATS_AUTOMATION_HOST_PATTERNS)


def effective_apply_url(row: dict) -> str:
    raw = (row.get("apply_url") or "").strip()
    main = (row.get("url") or "").strip()
    if raw and not is_blocked_listing_url(raw):
        return raw
    if main and not is_blocked_listing_url(main):
        return main
    if raw:
        return raw
    return main


EMAIL_ADDRESS_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)


def extract_emails_from_text(text: str) -> list[str]:
    if not (text or "").strip():
        return []
    seen: set[str] = set()
    out: list[str] = []
    for m in EMAIL_ADDRESS_PATTERN.finditer(text):
        e = m.group(0).strip().rstrip(".,;)")
        el = e.lower()
        if el not in seen:
            seen.add(el)
            out.append(e)
    return out[:20]


def valid_recruitment_email(addr: str) -> bool:
    a = (addr or "").strip().lower()
    if not a or "@" not in a:
        return False
    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", a):
        return False
    if any(
        x in a
        for x in (
            "noreply",
            "no-reply",
            "donotreply",
            "newsletter",
            "marketing@",
            "support@",
            "privacy@",
            "abuse@",
        )
    ):
        return False
    return True


def opportunity_has_employer_email(opportunity: dict) -> bool:
    return valid_recruitment_email((opportunity.get("contact_email") or "").strip())


def merge_opportunities_by_url(target: dict[str, dict], incoming: list[dict]) -> None:
    """Dedupe by listing URL; prefer rows that have a valid contact_email."""
    for row in incoming:
        key = (effective_apply_url(row) or "").strip()
        if not key.startswith("http"):
            continue
        prev = target.get(key)
        if prev is None:
            target[key] = dict(row)
            continue
        ne = (row.get("contact_email") or "").strip()
        pe = (prev.get("contact_email") or "").strip()
        if valid_recruitment_email(ne) and not valid_recruitment_email(pe):
            target[key] = dict(row)


EMAIL_DISCOVERY_QUERY_TWEAKS: tuple[str, ...] = (
    "Search tweak: emphasize .gov / government jobs / city or council career portals and civil-service listings that publish an HR or recruitment email.",
    "Search tweak: emphasize .edu universities, colleges, and research labs - vacancy pages that list a contact person or jobs@ / faculty-affairs email.",
    "Search tweak: emphasize charities, nonprofits, foundations, and NGOs - roles where the posting says to email a CV or shows jobs@ / hr@.",
    "Search tweak: emphasize employer-owned domains only - company careers pages, 'Work with us', and job PDFs that may list talent@ or careers@ in the footer.",
    "Search tweak: emphasize 'apply by email', 'send application to', 'applications to ...@', and regional or niche boards that quote the full employer text with an address.",
)

EMAIL_DISCOVERY_EXTRA_PASSES = 5


def row_is_recordable(row: dict) -> bool:
    title = (row.get("title") or "").strip()
    if not title:
        return False
    u = effective_apply_url(row)
    cem = (row.get("contact_email") or "").strip()
    if cem and valid_recruitment_email(cem):
        if u.startswith("http") and not is_blocked_listing_url(u):
            return True
    if not u.startswith("http"):
        return False
    if is_blocked_listing_url(u):
        return False
    return True


def ats_automation_ease_rank(url: str) -> int:
    """Lower = stronger ATS signal on the URL (used to order apply attempts)."""
    h = normalize_job_host(url)
    if "greenhouse.io" in h:
        return 0
    if "lever.co" in h:
        return 1
    if "ashbyhq.com" in h:
        return 2
    if "smartrecruiters.com" in h:
        return 3
    if "icims.com" in h or "bamboohr.com" in h:
        return 4
    if "workable.com" in h:
        return 6
    if "myworkdayjobs.com" in h:
        return 9
    return 5


def parse_json_array_payload(payload: str) -> list | None:
    """First JSON array in model output; strips ``` fences and trailing 'Extra data'."""
    s = (payload or "").strip()
    if not s:
        return None
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I | re.M)
        s = re.sub(r"\s*```\s*$", "", s).strip()
    try:
        dec = json.JSONDecoder()
        data, _ = dec.raw_decode(s)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    try:
        data = json.loads(s)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        return None


def html_to_plain_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()[:PAGE_CHARS]


def format_research_date_window() -> str:
    a, b = date.today(), date.today() + timedelta(days=WINDOW_DAYS - 1)
    return f"{a.isoformat()}-{b.isoformat()} ({WINDOW_DAYS}d)"


def openrouter_async_client() -> AsyncOpenAI:
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY")
    return AsyncOpenAI(base_url=OPENROUTER, api_key=api_key)


def openrouter_chat_model() -> OpenAIChatCompletionsModel:
    return OpenAIChatCompletionsModel(model=MODEL, openai_client=openrouter_async_client())


def format_candidate_profile_line(name: str, url: str) -> str:
    name, url = name.strip(), url.strip()
    return f"{name} | LinkedIn: {url}"


class ResearchAgentContext:
    def __init__(self, log: list[str] | None = None) -> None:
        serper_key = (os.getenv("SERPER_API_KEY") or "").strip()
        self.serper = GoogleSerperAPIWrapper(k=SERPER_K) if serper_key else None
        self.opportunities: list[dict] = []
        self.skipped: int = 0
        self.log = log


def append_research_log(context: ResearchAgentContext, message: str) -> None:
    if context.log is not None:
        context.log.append(message)


def build_research_tools(context: ResearchAgentContext):
    @function_tool
    async def search_google_queries(query: str) -> str:
        q = (query or "").strip()
        append_research_log(
            context,
            f"  search_google_queries: {q[:140]}{'...' if len(q) > 140 else ''}",
        )
        if not context.serper:
            return "SERPER_API_KEY missing"
        try:
            j = context.serper.results(query)
            lines = []
            for h in (j.get("organic") or [])[:SERPER_K]:
                lines.append(f"{h.get('title','')}\n{h.get('link','')}\n{h.get('snippet','')}\n")
            return "\n---\n".join(lines) if lines else "(empty)"
        except Exception as e:
            return str(e)

    @function_tool
    async def fetch_page_text(url: str) -> str:
        append_research_log(
            context,
            f"  fetch_page_text: {url[:120]}{'...' if len(url) > 120 else ''}",
        )
        if not url.startswith("http"):
            return "bad url"
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT, follow_redirects=True, headers=FETCH_HEADERS
        ) as c:
            try:
                r = await c.get(url)
            except httpx.RequestError:
                return f"[{url}] unreachable"

            if r.status_code == 200:
                text = html_to_plain_text(r.text)
                if text.strip():
                    return f"[{url}]\n{text}"
                return f"[{url}] empty"

            return f"[{url}] HTTP {r.status_code} - use Serper lines for this row."

    @function_tool
    async def extract_emails_from_url(page_url: str) -> str:
        """Fetch a job/careers page and return JSON array of plausible employer contact emails (no noreply)."""
        append_research_log(
            context,
            f"  extract_emails_from_url: {page_url[:120]}{'...' if len(page_url) > 120 else ''}",
        )
        if not page_url.startswith("http"):
            return "[]"
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT, follow_redirects=True, headers=FETCH_HEADERS
        ) as c:
            try:
                r = await c.get(page_url)
            except httpx.RequestError:
                return "[]"
            text = ""
            if r.status_code == 200 and (r.text or "").strip():
                text = html_to_plain_text(r.text)
        if not text.strip():
            return "[]"
        emails = [e for e in extract_emails_from_text(text) if valid_recruitment_email(e)]
        if not emails:
            return "[]"
        return json.dumps(list(dict.fromkeys(emails))[:5], ensure_ascii=False)

    @function_tool
    async def record_opportunities_json(payload: str) -> str:
        append_research_log(
            context,
            f"  record_opportunities_json: received {len(payload)} chars",
        )
        data = parse_json_array_payload(payload)
        if data is None:
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                append_research_log(
                    context,
                    f"  record_opportunities_json: JSON error - {e}",
                )
                return str(e)
        if not isinstance(data, list):
            append_research_log(context, "  record_opportunities_json: expected array")
            return "expected array"
        kept: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            row = {
                "title": str(item.get("title", "")).strip(),
                "url": str(item.get("url", "")).strip(),
                "apply_url": str(item.get("apply_url", "")).strip(),
                "deadline": str(item.get("deadline", "")).strip(),
                "type": str(item.get("type", "")).strip(),
                "contact_email": str(item.get("contact_email", "")).strip(),
                "apply_mode": str(item.get("apply_mode", "")).strip().lower(),
            }
            if not row["title"]:
                continue
            if not row_is_recordable(row):
                context.skipped += 1
                append_research_log(
                    context,
                    f"  skipped row (blocked URL): {row.get('title', '')[:60]}",
                )
                continue
            contact_email = row["contact_email"]
            mode = row["apply_mode"] or ""
            if not mode:
                mode = "email" if contact_email else "browser"
            kept.append(
                {
                    "title": row["title"],
                    "url": effective_apply_url(row),
                    "deadline": row["deadline"],
                    "type": row["type"],
                    "contact_email": contact_email,
                    "apply_mode": mode,
                }
            )
        context.opportunities = [r for r in kept if r["title"] and r["url"]]
        append_research_log(
            context,
            f"  record_opportunities_json: kept {len(context.opportunities)} job(s), "
            f"{context.skipped} skipped (blocked/invalid URLs)",
        )
        return json.dumps(
            {"n": len(context.opportunities), "skipped": context.skipped},
            ensure_ascii=False,
        )

    return [
        search_google_queries,
        fetch_page_text,
        extract_emails_from_url,
        record_opportunities_json,
    ]


def extract_focus_keywords(brief: str) -> str:
    """Role/location terms from the research brief."""
    tail = (brief or "").strip() or "software developer job"
    return tail[:220].strip()


def fallback_serper_email_jobs(brief: str, log: list[str]) -> list[dict]:
    """Serper results whose snippet/title contains a plausible hiring email."""
    k = (os.getenv("SERPER_API_KEY") or "").strip()
    if not k:
        log.append("  ... Email fallback: no SERPER_API_KEY")
        return []
    kw = extract_focus_keywords(brief)
    serper = GoogleSerperAPIWrapper(k=SERPER_K)
    queries = [
        f"{kw} job apply email CV hiring",
        f"{kw} careers email contact hiring",
        f'{kw} vacancy apply "@"',
        f"{kw} apply by email CV",
        f"{kw} government council civil service job vacancy email",
        f"{kw} charity NGO nonprofit job email apply",
        f"{kw} university research lab vacancy email careers",
    ]
    seen: set[str] = set()
    out: list[dict] = []
    for q in queries:
        if len(out) >= 8:
            break
        try:
            j = serper.results(q)
        except Exception:
            continue
        for h in (j.get("organic") or [])[:SERPER_K]:
            link = (h.get("link") or "").strip()
            title = (h.get("title") or "").strip()
            snippet = (h.get("snippet") or "").strip()
            if not link or not title or link in seen:
                continue
            pool = f"{snippet} {title}"
            emails = [e for e in extract_emails_from_text(pool) if valid_recruitment_email(e)]
            if not emails:
                continue
            row = {
                "title": title,
                "url": link,
                "apply_url": "",
                "deadline": "",
                "type": "job",
                "contact_email": emails[0],
                "apply_mode": "email",
            }
            if not row_is_recordable(row):
                continue
            seen.add(link)
            out.append(
                {
                    "title": title,
                    "url": effective_apply_url(row),
                    "deadline": "",
                    "type": "job",
                    "contact_email": emails[0],
                    "apply_mode": "email",
                }
            )
    log.append(f"  ... Email fallback Serper: {len(out)} job(s) with email in snippet/title")
    return out


def apply_attempt_rank(opportunity: dict) -> tuple[int, int, str]:
    """Sort: email rows first, then easier ATS."""
    title = opportunity.get("title") or ""
    if (opportunity.get("contact_email") or "").strip():
        return (0, ats_automation_ease_rank(effective_apply_url(opportunity)), title)
    return (1, ats_automation_ease_rank(effective_apply_url(opportunity)), title)


async def research_single_pass(
    name: str,
    url: str,
    brief: str,
    log: list[str],
    *,
    runner_prompt: str,
) -> tuple[list[dict], int]:
    log.append("  Model is using tools (each line below is a tool call).")
    context = ResearchAgentContext(log=log)
    profile_line = format_candidate_profile_line(name, url)
    common = (
        f"Individual job seeker: {profile_line}\nRequest: {brief}\nWindow: {format_research_date_window()}. "
        "Only include paid jobs or direct applications to employment (full-time, contract, internship). "
        "Exclude hackathons, accelerators, grants, generic events, unrelated tech posts. "
        "Do NOT use LinkedIn Jobs, Indeed, Glassdoor, ZipRecruiter, or similar as the sole apply URL. "
        "SOURCE PRIORITY (for finding contact_email): prefer (1) employer-owned career/job pages on the company domain "
        "(footer or JD often has careers@, talent@, hr@, jobs@); (2) public-sector portals "
        "(government, council, school district, civil service) that list an HR or hiring mailbox; "
        "(3) NGOs, charities, small businesses, local employers that say \"email your CV\" or list a contact; "
        "(4) universities and research labs (vacancy pages, jobs.ac.uk-style listings, faculty/staff openings); "
        "(5) industry or regional niche boards that repost full employer text including an email. "
        "De-prioritize mega-aggregator job boards; the strategy is sector + role + \"apply by email\" / contact discovery, "
        "not browsing famous job sites that hide addresses. "
    )
    instr = (
        common
        + "PRIMARY GOAL: find roles where the candidate can email the employer (careers@, hiring@, jobs@, etc.). "
        "Use search_google_queries with varied queries aligned to SOURCE PRIORITY: combine role/location/sector from the request with "
        "phrases like apply by email, send CV to, applications to, vacancy email, careers contact, HR email; "
        "add site: filters when helpful (e.g. site:.gov, site:.edu, site:.org, or a known employer domain careers path). "
        "Try public-sector and NGO/university wording (council job, civil service, charity vacancy, research assistant email) when the brief allows. "
        "Use extract_emails_from_url on non-blocked job or careers pages (including PDF/HTML JDs if linked) to set contact_email. "
        "Each JSON row: title, url (job posting page), deadline, type, optional apply_url, "
        "contact_email when found, apply_mode \"email\" when contact_email is set. "
        "You may still record rows without contact_email so the user sees the listing, but the app only sends email when contact_email is present. "
        "Reject noreply, no-reply, newsletter, marketing addresses. "
        "Do NOT set apply_mode \"api\" without real API documentation. "
        "You MUST call record_opportunities_json exactly once as a JSON array (no markdown). "
        "Every recorded url must be a non-blocked page. "
        "If zero qualifying roles, call record_opportunities_json with []."
    )
    agent = Agent(
        name="research",
        model=openrouter_chat_model(),
        tools=build_research_tools(context),
        instructions=instr,
    )
    with trace("research"):
        await Runner.run(agent, runner_prompt, max_turns=MAX_RESEARCH)
    opportunities = list(context.opportunities)
    skipped = context.skipped
    log.append(
        f"  Agent pass - {len(opportunities)} job(s) kept, {skipped} row(s) dropped (URL policy)."
    )
    if not opportunities:
        log.append("  ... No rows from agent - running Serper email fallback (snippet/title addresses only)")
        opportunities = await asyncio.to_thread(fallback_serper_email_jobs, brief, log)
    return opportunities, skipped


async def research_opportunities(
    name: str, url: str, brief: str, log: list[str]
) -> tuple[list[dict], int]:
    """
    Run research; if merged results still have no employer contact_email, retry up to
    EMAIL_DISCOVERY_EXTRA_PASSES times with an extra query tweak each time.
    """
    merged: dict[str, dict] = {}
    total_skipped = 0
    n_passes = 1 + EMAIL_DISCOVERY_EXTRA_PASSES

    for attempt in range(n_passes):
        if attempt == 0:
            log.append("=== Research agent (email-first) ===")
        else:
            log.append(
                f"=== Research retry {attempt}/{EMAIL_DISCOVERY_EXTRA_PASSES} "
                f"(no employer email in merged results - tweaked query) ==="
            )

        pass_brief = brief
        if attempt > 0:
            pass_brief = brief + " " + EMAIL_DISCOVERY_QUERY_TWEAKS[attempt - 1]

        if attempt == 0:
            runner_prompt = (
                "Run research using SOURCE PRIORITY (employer careers, public sector, NGO/small org, university, niche boards); "
                "finish with record_opportunities_json."
            )
        else:
            runner_prompt = (
                f"Retry {attempt} of {EMAIL_DISCOVERY_EXTRA_PASSES}: merged results still lack any row with a valid "
                "employer hiring/careers email. Follow the new Search tweak appended to the request. "
                "Try different search_google_queries strings (including site:.gov, site:.edu, site:.org) and "
                "extract_emails_from_url on pages likely to show HR or recruitment addresses. "
                "Finish with record_opportunities_json."
            )

        batch, skipped = await research_single_pass(
            name, url, pass_brief, log, runner_prompt=runner_prompt
        )
        total_skipped += skipped
        merge_opportunities_by_url(merged, batch)
        combined = list(merged.values())
        rows_with_email = sum(
            1 for row in combined if opportunity_has_employer_email(row)
        )
        if rows_with_email > 0:
            log.append(
                f"  Employer email present in {rows_with_email} row(s) after pass {attempt + 1}/{n_passes} - stopping retries."
            )
            break
        if attempt < n_passes - 1:
            log.append(
                f"  ... Still no employer email in {len(combined)} merged listing(s); running another pass."
            )

    with_email = sum(
        1 for row in merged.values() if opportunity_has_employer_email(row)
    )
    log.append(
        f"  Research finished - {len(merged)} unique job(s) ({with_email} with employer email)."
    )
    return list(merged.values()), total_skipped
