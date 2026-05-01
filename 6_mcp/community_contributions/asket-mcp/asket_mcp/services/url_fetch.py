from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

import httpx

from asket_mcp.config import get_settings


def _host_is_safe(hostname: str) -> bool:
    h = hostname.strip().lower()
    if not h or h == "localhost":
        return False
    if h.startswith("["):
        return False
    try:
        ip = ipaddress.ip_address(h)
        return ip.is_global
    except ValueError:
        pass
    blocked_suffixes = (".localhost", ".local", ".internal", ".lan")
    return not any(h.endswith(s) for s in blocked_suffixes)


def _strip_html_loose(raw: bytes, max_chars: int) -> str:
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode(errors="replace")
    text = re.sub(r"(?is)<script.*?>.*?</script>", "", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def fetch_url_text(url: str) -> str:
    settings = get_settings()
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are allowed.")
    if not parsed.hostname:
        raise ValueError("Invalid URL.")
    if not _host_is_safe(parsed.hostname):
        raise ValueError("URL host is not allowed (private or local addresses blocked).")

    timeout = httpx.Timeout(settings.httpx_timeout_seconds)
    headers = {"User-Agent": settings.fetch_user_agent}
    cap = settings.fetch_max_bytes
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        r = client.get(url)
        r.raise_for_status()
        raw = r.content[: cap + 64_000]

    ctype = (r.headers.get("content-type") or "").lower()
    if "text/html" in ctype or url.lower().endswith((".htm", ".html")):
        return _strip_html_loose(raw, cap)
    try:
        return raw.decode("utf-8", errors="replace")[:cap]
    except Exception:
        return raw.decode(errors="replace")[:cap]
