from __future__ import annotations

import ast
import ipaddress
import operator
import os
import re
from urllib.parse import urlparse
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from langchain_core.tools import Tool, tool
from langchain_community.agent_toolkits import FileManagementToolkit, PlayWrightBrowserToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_experimental.tools import PythonREPLTool
from playwright.async_api import async_playwright

import socket
from datetime import datetime, timezone
from email.utils import parseaddr
from html import unescape

import dns.resolver
import idna
import tldextract
import whois
from bs4 import BeautifulSoup

from task_store import list_recent_tasks, save_task

load_dotenv(override=True)

pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_user = os.getenv("PUSHOVER_USER")
pushover_url = "https://api.pushover.net/1/messages.json"

_serper = None


def _serper_run(query: str) -> str:
    global _serper
    if _serper is None:
        try:
            _serper = GoogleSerperAPIWrapper()
        except Exception as e:
            return f"Web search unavailable (configure SERPER_API_KEY): {e}"
    try:
        return _serper.run(query)
    except Exception as e:
        return f"Search failed: {e}"


def push(text: str) -> str:
    """Send a push notification (requires PUSHOVER_TOKEN and PUSHOVER_USER)."""
    if not pushover_token or not pushover_user:
        return "Pushover not configured."
    requests.post(pushover_url, data={"token": pushover_token, "user": pushover_user, "message": text})
    return "success"


def fetch_url_text(url: str, max_chars: int = 12000) -> str:
    """Fetch a URL and return visible text (no JS). Lighter than a full browser for static pages."""
    parsed = urlparse((url or "").strip())
    hostname = parsed.hostname
    if parsed.scheme not in {"http", "https"} or not hostname:
        return "Blocked: only valid http/https URLs are allowed."
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return "Blocked: private, loopback, and internal network addresses are not allowed."
    except ValueError:
        lowered = hostname.lower()
        if lowered in {"localhost", "host.docker.internal"} or lowered.endswith(".local"):
            return "Blocked: localhost and internal hostnames are not allowed."
    headers = {"User-Agent": "SidekickResearchBot/1.0 (educational)"}
    resp = requests.get(url, timeout=20, headers=headers)
    resp.raise_for_status()
    raw = resp.text
    raw = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", raw)
    raw = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", raw)
    raw = re.sub(r"(?is)<noscript[^>]*>.*?</noscript>", " ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text) > max_chars:
        return text[:max_chars] + "\n...[truncated]"
    return text


def _safe_eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants allowed")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        v = _safe_eval(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp):
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }
        op_type = type(node.op)
        if op_type not in ops:
            raise ValueError("Operator not allowed")
        return ops[op_type](left, right)
    raise ValueError("Expression not allowed")


def calculate_math(expression: str) -> str:
    """Safely evaluate a numeric expression with + - * / ** % and parentheses. No names or calls."""
    expr = (expression or "").strip()
    if not expr:
        return "Empty expression"
    tree = ast.parse(expr, mode="eval")
    try:
        return str(_safe_eval(tree.body))
    except Exception as e:
        return f"Could not evaluate: {e}"


PYTHON_BLOCK_PATTERNS = [
    r"\bimport\s+os\b",
    r"\bimport\s+sys\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+socket\b",
    r"\bimport\s+shutil\b",
    r"\bimport\s+requests\b",
    r"\bfrom\s+os\s+import\b",
    r"\bfrom\s+subprocess\s+import\b",
    r"\bos\.environ\b",
    r"\bsubprocess\.",
    r"\bsocket\.",
    r"\bopen\s*\(",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"__import__\s*\(",
    r"\bpip\s+install\b",
    r"\brm\s+-rf\b",
]


def guarded_python(code: str) -> str:
    snippet = (code or "").strip()
    if not snippet:
        return "Blocked: empty Python input."
    for pattern in PYTHON_BLOCK_PATTERNS:
        if re.search(pattern, snippet, flags=re.IGNORECASE):
            return "Blocked by guardrails: unsafe Python code or system access was requested."
    python_repl = PythonREPLTool()
    try:
        return str(python_repl.run(snippet))
    except Exception as e:
        return f"Python execution failed: {e}"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()


async def playwright_tools():
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "").lower() in ("1", "true", "yes")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright


def build_research_tools(username_getter: Callable[[], str]) -> list:
    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)
    search_tool = Tool(
        name="search",
        func=_serper_run,
        description="Web search for current facts, links, and snippets (Google Serper).",
    )

    def save_my_task(title: str, summary: str = "") -> str:
        return save_task(username_getter(), title, summary or title)

    tools: list = [
        search_tool,
        wiki_tool,
        Tool(
            name="fetch_url_text",
            func=fetch_url_text,
            description="HTTP GET a URL and return plain text (good for docs, static HTML). Max ~12k chars.",
        ),
        Tool(
            name="list_my_recent_tasks",
            func=lambda _q: list_recent_tasks(username_getter()),
            description="List this user's recently saved tasks from the task library (same username as login). Pass any short query or leave blank.",
        ),
        Tool(
            name="save_task_to_library",
            func=save_my_task,
            description="Save a short title and summary of the current assignment to the user's task library for later.",
        ),
    ]
    if pushover_token and pushover_user:
        tools.append(
            Tool(
                name="send_push_notification",
                func=push,
                description="Send a push notification to the user via Pushover.",
            )
        )
    return tools


def build_files_tools(username_getter: Callable[[], str]) -> list:
    def save_my_task(title: str, summary: str = "") -> str:
        return save_task(username_getter(), title, summary or title)

    return get_file_tools() + [
        Tool(
            name="guarded_python",
            func=guarded_python,
            description="Run low-risk Python snippets for calculations or text/data transforms. Dangerous imports, file access, env access, subprocesses, and networking are blocked.",
        ),
        Tool(
            name="calculate_math",
            func=calculate_math,
            description="Evaluate a numeric expression only, e.g. '(2 + 3) * 4 ** 0.5'. No variables or functions.",
        ),
        Tool(
            name="save_task_to_library",
            func=save_my_task,
            description="Save a short title and summary of work to the user's persistent task library.",
        ),
    ]

# Business Email Compromise (BEC) Tools (Cybersecurity Tools)

# =========================
# Helpers
# =========================

RECENT_DAYS_DEFAULT = 90

KEYBOARD_ADJACENCY = {
    "a": "qwsz",
    "b": "vghn",
    "c": "xdfv",
    "d": "erfcxs",
    "e": "rdsw",
    "f": "rtgvcd",
    "g": "tyhbvf",
    "h": "yujnbg",
    "i": "uojk",
    "j": "uikmnh",
    "k": "iolmj",
    "l": "opk",
    "m": "njk",
    "n": "bhjm",
    "o": "pikl",
    "p": "ol",
    "q": "wa",
    "r": "tfde",
    "s": "wedxza",
    "t": "ygfr",
    "u": "yihj",
    "v": "cfgb",
    "w": "qase",
    "x": "zsdc",
    "y": "uhgt",
    "z": "asx",
}

HOMOGLYPHS = {
    "o": ["0"],
    "l": ["1", "i"],
    "i": ["1", "l"],
    "e": ["3"],
    "a": ["4"],
    "s": ["5"],
    "g": ["9"],
    "b": ["8"],
    "m": ["rn"],
    "w": ["vv"],
}

COMMON_TLD_SWAPS = ["com", "net", "org", "co", "io", "ai", "biz", "com.ng"]

EXECUTIVE_TITLES = {
    "ceo", "cto", "cfo", "coo", "founder", "president", "director", "manager", "vp"
}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_domain(domain: str) -> str:
    domain = domain.strip().lower()

    if "://" in domain:
        domain = urlparse(domain).netloc

    domain = domain.split("/")[0].split(":")[0].strip(".")
    if not domain:
        raise ValueError("Invalid domain input")

    return idna.encode(domain).decode("ascii")


def get_registered_domain(domain: str) -> Tuple[str, str]:
    ext = tldextract.extract(domain)
    if not ext.domain or not ext.suffix:
        raise ValueError(f"Could not determine registered domain for: {domain}")
    registered = f"{ext.domain}.{ext.suffix}"
    return registered, ext.suffix


def parse_creation_date(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, list):
        candidates = [v for v in value if v]
        if not candidates:
            return None
        value = min(candidates)

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, str):
        for fmt in (
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
            "%d-%b-%Y",
        ):
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue

    return None


def safe_whois_lookup(domain: str) -> Dict[str, Any]:
    try:
        w = whois.whois(domain)
        created = parse_creation_date(getattr(w, "creation_date", None))
        expiration = parse_creation_date(getattr(w, "expiration_date", None))
        registrar = getattr(w, "registrar", None)
        name_servers = getattr(w, "name_servers", None)
        return {
            "domain": domain,
            "created_at": created.isoformat() if created else None,
            "created_at_dt": created,
            "expires_at": expiration.isoformat() if expiration else None,
            "registrar": registrar,
            "name_servers": list(name_servers) if isinstance(name_servers, (list, set, tuple)) else name_servers,
            "raw_available": True,
        }
    except Exception as e:
        return {
            "domain": domain,
            "created_at": None,
            "created_at_dt": None,
            "expires_at": None,
            "registrar": None,
            "name_servers": None,
            "raw_available": False,
            "error": str(e),
        }


def domain_age_days(created_at: Optional[datetime]) -> Optional[int]:
    if not created_at:
        return None
    return (utcnow() - created_at).days


def has_dns_record(name: str, record_type: str) -> bool:
    try:
        dns.resolver.resolve(name, record_type, lifetime=3.0)
        return True
    except Exception:
        return False


def get_dns_records(name: str, record_type: str) -> List[str]:
    try:
        answers = dns.resolver.resolve(name, record_type, lifetime=3.0)
        return [str(r).strip() for r in answers]
    except Exception:
        return []


def extract_domain_from_email(address: str) -> Optional[str]:
    _, email_addr = parseaddr(address)
    if "@" not in email_addr:
        return None
    return normalize_domain(email_addr.split("@", 1)[1])


def levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + cost,
            ))
        prev = curr
    return prev[-1]


def generate_lookalike_domains(domain: str, max_variants: int = 200) -> List[str]:
    registered_domain, suffix = get_registered_domain(domain)
    ext = tldextract.extract(registered_domain)
    label = ext.domain

    candidates = set()
    # omission
    for i in range(len(label)):
        mutated = label[:i] + label[i + 1:]
        if len(mutated) >= 3:
            candidates.add(f"{mutated}.{suffix}")

    # transposition
    for i in range(len(label) - 1):
        chars = list(label)
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
        candidates.add(f"{''.join(chars)}.{suffix}")

    # keyboard adjacency replacements
    for i, ch in enumerate(label):
        for repl in KEYBOARD_ADJACENCY.get(ch, ""):
            mutated = label[:i] + repl + label[i + 1:]
            candidates.add(f"{mutated}.{suffix}")

    # homoglyphs
    for i, ch in enumerate(label):
        for repl in HOMOGLYPHS.get(ch, []):
            mutated = label[:i] + repl + label[i + 1:]
            candidates.add(f"{mutated}.{suffix}")

    # hyphen insertion
    for i in range(1, len(label)):
        mutated = label[:i] + "-" + label[i:]
        candidates.add(f"{mutated}.{suffix}")

    # TLD swaps
    for tld in COMMON_TLD_SWAPS:
        if tld != suffix:
            candidates.add(f"{label}.{tld}")

    # drop original
    candidates.discard(registered_domain)

    ranked = sorted(
        candidates,
        key=lambda d: levenshtein_distance(label, tldextract.extract(d).domain)
    )

    return ranked[:max_variants]


def extract_urls_from_text(text: str) -> List[str]:
    urls = set()

    # raw URLs
    raw_pattern = r"""(?i)\b((?:https?://|www\.)[^\s<>"']+)"""
    for match in re.findall(raw_pattern, text or ""):
        url = match.strip(").,;\"'")
        if url.startswith("www."):
            url = "http://" + url
        urls.add(url)

    # HTML hrefs
    try:
        soup = BeautifulSoup(text or "", "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith(("http://", "https://")):
                urls.add(href)
    except Exception:
        pass

    return sorted(urls)


def is_private_or_internal_domain(domain: str) -> bool:
    return domain.endswith(".local") or domain.endswith(".internal")


# =========================
# Tool 1: Domain Age
# =========================

@tool
def check_domain_age(domain: str, suspicious_threshold_days: int = 90) -> Dict[str, Any]:
    """
    Check a domain's registration age.
    Useful for BEC because newly registered domains are commonly used
    for phishing, vendor fraud, and executive impersonation.
    """
    normalized = normalize_domain(domain)
    info = safe_whois_lookup(normalized)
    created_dt = info.get("created_at_dt")
    age = domain_age_days(created_dt)

    return {
        "domain": normalized,
        "created_at": info.get("created_at"),
        "domain_age_days": age,
        "is_new_domain": age is not None and age < suspicious_threshold_days,
        "suspicious_threshold_days": suspicious_threshold_days,
        "registrar": info.get("registrar"),
        "name_servers": info.get("name_servers"),
        "notes": (
            "WHOIS/RDAP coverage varies by TLD. Missing creation date should be treated as inconclusive, not safe."
        ),
        "error": info.get("error"),
    }


# =========================
# Tool 2: Recent Look-Alike Domains
# =========================

@tool
def find_recent_lookalike_domains(
    domain: str,
    recent_days: int = 90,
    max_variants: int = 50,
    only_registered: bool = True,
) -> Dict[str, Any]:
    """
    Generate likely look-alike domains for a brand/domain and check whether
    any appear newly registered.
    This can help detect typo-squatting and BEC infrastructure.
    """
    normalized = normalize_domain(domain)
    variants = generate_lookalike_domains(normalized, max_variants=max_variants)

    findings: List[Dict[str, Any]] = []

    for candidate in variants:
        info = safe_whois_lookup(candidate)
        created_dt = info.get("created_at_dt")
        age = domain_age_days(created_dt)

        # Quick infrastructure checks can help prioritize
        has_a = has_dns_record(candidate, "A")
        has_mx = has_dns_record(candidate, "MX")
        has_txt = has_dns_record(candidate, "TXT")

        if only_registered and not created_dt and not (has_a or has_mx or has_txt):
            continue

        if age is not None and age <= recent_days:
            findings.append({
                "domain": candidate,
                "created_at": info.get("created_at"),
                "domain_age_days": age,
                "registrar": info.get("registrar"),
                "has_a_record": has_a,
                "has_mx_record": has_mx,
                "has_txt_record": has_txt,
                "looks_recent": True,
            })
        elif not only_registered and (has_a or has_mx or has_txt):
            findings.append({
                "domain": candidate,
                "created_at": info.get("created_at"),
                "domain_age_days": age,
                "registrar": info.get("registrar"),
                "has_a_record": has_a,
                "has_mx_record": has_mx,
                "has_txt_record": has_txt,
                "looks_recent": age is not None and age <= recent_days,
            })

    findings.sort(key=lambda x: (x["domain_age_days"] is None, x["domain_age_days"] or 999999))

    return {
        "brand_domain": normalized,
        "recent_days": recent_days,
        "checked_variants": len(variants),
        "recent_lookalikes_found": len(findings),
        "findings": findings,
        "notes": (
            "This is a heuristic detector."
        ),
    }


# =========================
# Tool 3: Email Auth / Domain Posture
# =========================

@tool
def check_email_auth_posture(domain: str) -> Dict[str, Any]:
    """
    Check DNS-based email posture for a domain:
    MX, SPF, and DMARC. To detect Weak or missing controls.
    """
    normalized = normalize_domain(domain)

    mx_records = get_dns_records(normalized, "MX")
    txt_records = get_dns_records(normalized, "TXT")
    dmarc_records = get_dns_records(f"_dmarc.{normalized}", "TXT")

    spf_records = [r for r in txt_records if r.lower().startswith("v=spf1")]
    dmarc_valid = [r for r in dmarc_records if r.lower().startswith("v=dmarc1")]

    return {
        "domain": normalized,
        "has_mx": len(mx_records) > 0,
        "mx_records": mx_records,
        "has_spf": len(spf_records) > 0,
        "spf_records": spf_records,
        "has_dmarc": len(dmarc_valid) > 0,
        "dmarc_records": dmarc_valid,
        "risk_flags": {
            "missing_mx": len(mx_records) == 0,
            "missing_spf": len(spf_records) == 0,
            "missing_dmarc": len(dmarc_valid) == 0,
        },
        "notes": "DKIM validation usually requires message headers and selector information, not just the domain.",
    }


def build_bec_tools() -> list:
    """BEC / domain posture tools for the dedicated BEC specialist."""
    return [
        check_domain_age,
        find_recent_lookalike_domains,
        check_email_auth_posture,
    ]


# # =========================
# # Tool 4: Reply-To Mismatch
# # =========================

# @tool
# def detect_reply_to_mismatch(from_address: str, reply_to_address: str) -> Dict[str, Any]:
#     """
#     Detect whether Reply-To points to a different domain than From.
#     This is a classic BEC/phishing trick.
#     """
#     from_domain = extract_domain_from_email(from_address)
#     reply_to_domain = extract_domain_from_email(reply_to_address)

#     mismatch = (
#         from_domain is not None and
#         reply_to_domain is not None and
#         from_domain != reply_to_domain
#     )

#     return {
#         "from_address": from_address,
#         "reply_to_address": reply_to_address,
#         "from_domain": from_domain,
#         "reply_to_domain": reply_to_domain,
#         "domain_mismatch": mismatch,
#         "risk_level": "high" if mismatch else "low",
#         "notes": "A mismatch is not always malicious, but it deserves investigation in payment, invoice, or credential-related emails.",
#     }


# # =========================
# # Tool 5: Suspicious URL Inspection
# # =========================

# @tool
# def inspect_urls_in_email(email_body: str, expected_sender_domain: Optional[str] = None) -> Dict[str, Any]:
#     """
#     Extract URLs from an email and flag:
#     - punycode domains
#     - mismatched expected brand/sender domain
#     - URL shorteners
#     """
#     urls = extract_urls_from_text(unescape(email_body))
#     shorteners = {
#         "bit.ly", "tinyurl.com", "t.co", "ow.ly", "rb.gy", "buff.ly", "cutt.ly"
#     }

#     results = []
#     expected_domain = normalize_domain(expected_sender_domain) if expected_sender_domain else None

#     for url in urls:
#         parsed = urlparse(url)
#         host = parsed.netloc.lower().split(":")[0]
#         if not host:
#             continue

#         try:
#             normalized_host = normalize_domain(host)
#         except Exception:
#             normalized_host = host

#         is_punycode = normalized_host.startswith("xn--")
#         is_shortener = normalized_host in shorteners

#         mismatched_brand = False
#         if expected_domain:
#             try:
#                 expected_registered, _ = get_registered_domain(expected_domain)
#                 observed_registered, _ = get_registered_domain(normalized_host)
#                 mismatched_brand = expected_registered != observed_registered
#             except Exception:
#                 mismatched_brand = normalized_host != expected_domain

#         results.append({
#             "url": url,
#             "host": normalized_host,
#             "is_punycode": is_punycode,
#             "is_shortener": is_shortener,
#             "mismatched_expected_sender_domain": mismatched_brand,
#         })

#     suspicious_count = sum(
#         1 for r in results
#         if r["is_punycode"] or r["is_shortener"] or r["mismatched_expected_sender_domain"]
#     )

#     return {
#         "url_count": len(results),
#         "suspicious_url_count": suspicious_count,
#         "urls": results,
#     }


# # =========================
# # Tool 6: Executive / VIP Impersonation
# # =========================

# @tool
# def detect_executive_impersonation(
#     display_name: str,
#     from_address: str,
#     trusted_people: List[Dict[str, str]],
# ) -> Dict[str, Any]:
#     """
#     Check whether the display name matches a trusted executive/person,
#     but the sender domain does not match that person's legitimate domain.

#     trusted_people example:
#     [
#         {"name": "Jane Doe", "email": "jane.doe@company.com", "title": "CEO"},
#         {"name": "John Smith", "email": "john.smith@company.com", "title": "CFO"}
#     ]
#     """
#     sender_domain = extract_domain_from_email(from_address)
#     normalized_display = re.sub(r"\s+", " ", display_name.strip().lower())

#     matches = []

#     for person in trusted_people:
#         trusted_name = person.get("name", "").strip().lower()
#         trusted_email = person.get("email", "").strip().lower()
#         trusted_title = person.get("title", "").strip().lower()
#         trusted_domain = extract_domain_from_email(trusted_email) if trusted_email else None

#         name_match = trusted_name and trusted_name == normalized_display
#         title_hint = trusted_title in EXECUTIVE_TITLES

#         if name_match:
#             matches.append({
#                 "matched_person": person,
#                 "sender_domain": sender_domain,
#                 "trusted_domain": trusted_domain,
#                 "domain_mismatch": sender_domain != trusted_domain if sender_domain and trusted_domain else None,
#                 "is_executive_or_vip": title_hint,
#             })

#     suspicious = any(m["domain_mismatch"] for m in matches if m["domain_mismatch"] is not None)

#     return {
#         "display_name": display_name,
#         "from_address": from_address,
#         "possible_matches": matches,
#         "likely_impersonation": suspicious,
#         "notes": "Very useful for fake CEO/CFO invoice, gift card, payroll, and urgent wire-transfer requests.",
#     }