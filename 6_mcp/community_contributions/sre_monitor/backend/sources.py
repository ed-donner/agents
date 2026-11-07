import asyncio
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

from .settings import ServiceConfig, ssl_context

RESOLVED_STATUSES = {"resolved", "postmortem", "completed", "remediated", "cancelled"}
IMPACT_RANK = {"none": 0, "unknown": 0, "maintenance": 0, "minor": 1, "major": 2, "critical": 3}
HEADERS = {"User-Agent": "sre-monitor/1.0"}
TIMEOUT = 20
PAGE_TEXT_LIMIT = 6000

_detected_types: dict[str, str] = {}


class Incident(BaseModel):
    service: str
    incident_id: str
    name: str
    status: str
    impact: str = "unknown"
    link: str
    components: list[str] = []
    updates: list[str] = []
    created_at: datetime
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    @property
    def key(self) -> str:
        return f"{self.service}:{self.incident_id}"

    @property
    def is_open(self) -> bool:
        return self.status not in RESOLVED_STATUSES


class ServiceSnapshot(BaseModel):
    service: str
    url: str
    indicator: str = "unknown"
    description: str = ""
    degraded_components: list[str] = []
    incidents: list[Incident] = []
    error: str | None = None


def clean_text(value: str, limit: int = 600) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def origin(url: str) -> str:
    """The site root, so a page such as /history or /zscaler.net/incidents still reaches the API."""
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _statuspage_incident(service: ServiceConfig, base: str, raw: dict) -> Incident:
    updates = [
        f"{(update.get('created_at') or '')[:16]} [{update.get('status')}] {clean_text(update.get('body', ''))}"
        for update in (raw.get("incident_updates") or [])[:5]
    ]
    return Incident(
        service=service.name,
        incident_id=raw["id"],
        name=raw["name"],
        status=(raw.get("status") or "unknown").lower(),
        impact=(raw.get("impact") or "none").lower(),
        link=f"{base}/incidents/{raw['id']}",
        components=[component["name"] for component in raw.get("components") or []],
        updates=updates,
        created_at=parse_time(raw.get("created_at")) or datetime.now(timezone.utc),
        updated_at=parse_time(raw.get("updated_at")),
        resolved_at=parse_time(raw.get("resolved_at")),
    )


ZSCALER_API = "https://trust.zscaler.com/api/incident"
ZSCALER_MAX_PAGES = 3
ZSCALER_IMPACT = {
    "service disruption": "major",
    "service degradation": "minor",
    "under investigation": "minor",
}
ZSCALER_TIME = "%Y-%m-%d %H:%M:%S"


def _zscaler_time(value: str | None) -> datetime | None:
    if not value or value == "None":
        return None
    try:
        return datetime.strptime(value, ZSCALER_TIME).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _zscaler_incident(service: ServiceConfig, record: dict, severity_names: dict[str, str]) -> Incident:
    section = urlparse(service.url).path.strip("/").split("/")[0] or "zscaler.net"
    severity = severity_names.get(str(record.get("severityId")), "").lower()
    posted = record.get("posted_on")
    created = (parsedate_to_datetime(posted) if posted else None) or _zscaler_time(record.get("created"))
    updates = []
    if impact := clean_text(record.get("customer_impact") or ""):
        updates.append(f"Customer impact: {impact}")
    if body := clean_text(record.get("body") or "", 800):
        updates.append(body)
    if cancel := clean_text(record.get("cancel_note") or ""):
        updates.append(f"Cancelled: {cancel}")
    alias = record.get("alias") or f"/posts/{record['id']}"
    return Incident(
        service=service.name,
        incident_id=str(record["id"]),
        name=record.get("title") or "Untitled incident",
        status=(record.get("status") or "unknown").lower(),
        impact=ZSCALER_IMPACT.get(severity, "none"),
        link=f"{origin(service.url)}/{section}{alias}",
        updates=updates[:5],
        created_at=created or datetime.now(timezone.utc),
        updated_at=_zscaler_time(record.get("updated")),
        resolved_at=_zscaler_time(record.get("resolved_date")),
    )


async def _fetch_zscaler(client: httpx.AsyncClient, service: ServiceConfig) -> ServiceSnapshot:
    """Zscaler Trust Portal: a JSON API behind its JavaScript site, paged and keyed by cloud id."""
    if not service.cloud:
        raise ValueError("type zscaler needs a cloud id, for example zsn")
    incidents: list[Incident] = []
    severity_names: dict[str, str] = {}
    page, total_pages = 1, 1
    while page <= min(total_pages, ZSCALER_MAX_PAGES):
        response = await client.get(
            ZSCALER_API,
            params={"cloud": service.cloud, "page": page},
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data = response.json()["data"]
        total_pages = int(data.get("totalPages") or 1)
        severity_names.update({str(item["tid"]): item["name"] for item in data.get("severity") or []})
        for record in data.get("records") or []:
            if str(record.get("published")) == "1":
                incidents.append(_zscaler_incident(service, record, severity_names))
        page += 1
    open_now = [incident for incident in incidents if incident.is_open]
    indicator = next((level for level in ("critical", "major", "minor") if any(i.impact == level for i in open_now)), "none")
    return ServiceSnapshot(
        service=service.name,
        url=service.url,
        indicator=indicator,
        description=f"{len(open_now)} open incident(s)" if open_now else "No open incidents",
        incidents=incidents,
    )


async def _fetch_statuspage(client: httpx.AsyncClient, service: ServiceConfig) -> ServiceSnapshot:
    base = origin(service.url)
    summary_response, incidents_response = await asyncio.gather(
        client.get(f"{base}/api/v2/summary.json"), client.get(f"{base}/api/v2/incidents.json")
    )
    summary_response.raise_for_status()
    incidents_response.raise_for_status()
    summary = summary_response.json()
    status = summary.get("status") or {}
    degraded = [
        component["name"]
        for component in summary.get("components") or []
        if component.get("status") not in (None, "operational") and not component.get("group")
    ]
    return ServiceSnapshot(
        service=service.name,
        url=service.url,
        indicator=status.get("indicator") or "unknown",
        description=status.get("description") or "",
        degraded_components=degraded[:30],
        incidents=[
            _statuspage_incident(service, base, raw)
            for raw in incidents_response.json().get("incidents") or []
        ],
    )


async def _fetch_rss(client: httpx.AsyncClient, service: ServiceConfig) -> ServiceSnapshot:
    feed_url = service.feed_url or f"{origin(service.url)}/history.rss"
    response = await client.get(feed_url)
    response.raise_for_status()
    incidents = []
    for item in ET.fromstring(response.content).iter("item"):
        if (item.findtext("category") or "").lower() == "maintenance":
            continue
        description = html.unescape(item.findtext("description") or "")
        status_match = re.search(r"<strong>([^<]+)</strong>", description)
        published = item.findtext("pubDate")
        created = parsedate_to_datetime(published) if published else datetime.now(timezone.utc)
        link = item.findtext("link") or service.url
        incidents.append(
            Incident(
                service=service.name,
                incident_id=item.findtext("guid") or link,
                name=item.findtext("title") or "Untitled incident",
                status=status_match.group(1).strip().lower() if status_match else "unknown",
                link=link,
                updates=[clean_text(part) for part in description.split("</p>") if clean_text(part)][:5],
                created_at=created,
                updated_at=created,
            )
        )
    recent = datetime.now(timezone.utc) - timedelta(hours=24)
    active = [incident for incident in incidents if incident.is_open and incident.created_at >= recent]
    return ServiceSnapshot(
        service=service.name,
        url=service.url,
        indicator="minor" if active else "none",
        description=f"{len(active)} open incident(s)" if active else "No open incidents in the feed",
        incidents=incidents,
    )


async def fetch_service(client: httpx.AsyncClient, service: ServiceConfig) -> ServiceSnapshot:
    kind = service.type if service.type != "auto" else _detected_types.get(service.name, "auto")
    try:
        if kind == "zscaler":
            return await _fetch_zscaler(client, service)
        if kind in ("auto", "statuspage"):
            try:
                snapshot = await _fetch_statuspage(client, service)
                _detected_types[service.name] = "statuspage"
                return snapshot
            except (httpx.HTTPError, ValueError):
                if kind == "statuspage":
                    raise
        snapshot = await _fetch_rss(client, service)
        _detected_types[service.name] = "rss"
        return snapshot
    except Exception as exc:
        return ServiceSnapshot(
            service=service.name,
            url=service.url,
            description="Could not read the status page",
            error=f"{type(exc).__name__}: {exc}"[:300],
        )


async def fetch_all(services: list[ServiceConfig]) -> list[ServiceSnapshot]:
    async with httpx.AsyncClient(
        verify=ssl_context(), timeout=TIMEOUT, headers=HEADERS, follow_redirects=True
    ) as client:
        return await asyncio.gather(*(fetch_service(client, service) for service in services))


def read_page_text(url: str) -> str:
    """Visible text of a web page, starting near any postmortem section."""
    if not url.startswith(("https://", "http://")):
        return "Only http(s) URLs can be read."
    try:
        response = httpx.get(
            url, verify=ssl_context(), timeout=TIMEOUT, headers=HEADERS, follow_redirects=True
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Could not read {url}: {exc}"
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
        tag.decompose()
    text = re.sub(r"\n\s*\n+", "\n\n", soup.get_text("\n")).strip()
    marker = re.search(r"post[- ]?mortem|root cause", text, re.IGNORECASE)
    start = max(0, marker.start() - 500) if marker else 0
    return text[start : start + PAGE_TEXT_LIMIT]
