"""The SRE agent team, wired as a LangGraph of handoffs.

The orchestrator is a model that decides which specialist to hand the work to next. Every
specialist hands control back to the orchestrator with a Command when it finishes, so each
transfer of control is a handoff rather than a fixed edge.
"""

import asyncio
import json
import operator
from datetime import datetime
from html import escape
from typing import Annotated, Literal, TypedDict

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from langsmith import traceable
from pydantic import BaseModel, Field

from . import store
from .emailer import PUSH_SEVERITIES, recipients, send_email, send_push
from .email_templates import markdown_to_email_html, shell
from .settings import PROJECT_DIR, get_llm, get_settings, model_label
from .sources import read_page_text
from .serper import search_incident_evidence
from .prompts import (
    ORCHESTRATOR_PROMPT,
    WATCHER_PROMPT,
    TRIAGE_PROMPT,
    IMPACT_VERIFIER_PROMPT,
    NOTIFIER_PROMPT,
    POSTMORTEM_PROMPT,
    DAILY_REVIEW_EMAIL_NOTE,
)

REPORTS_DIR = PROJECT_DIR / "reports"
MAX_ORCHESTRATOR_TURNS = 8
SEVERITY_COLOURS = {"SEV1": "#c0392b", "SEV2": "#e67e22", "SEV3": "#f1c40f", "SEV4": "#7f8c8d"}

NextStep = Literal[
    "status_watcher", "triage", "impact_verifier", "postmortem_analyst", "notifier", "finish"
]


class MonitorState(TypedDict, total=False):
    mode: Literal["incident_alert", "daily_review"]
    dry_run: bool
    candidates: list[dict]
    reports: list[dict]
    triage: list[dict]
    verification: list[dict]
    report_markdown: str
    report_path: str
    emails: list[dict]
    handoffs: Annotated[list[str], operator.add]
    turns: int


class Handoff(BaseModel):
    next_agent: NextStep = Field(description="The specialist to hand the work to next, or finish")
    reason: str = Field(description="One sentence explaining the handoff")


class IncidentReport(BaseModel):
    key: str = Field(description="The entry's key, copied exactly")
    is_service_incident: bool = Field(
        description="False only for scheduled maintenance, tests or notices with no customer impact"
    )
    summary: str = Field(description="2-3 sentences: what is broken, who or where is affected, current status")
    affected: list[str] = Field(description="Affected products, components or regions")


class WatchReport(BaseModel):
    reports: list[IncidentReport]


class TriageDecision(BaseModel):
    key: str = Field(description="The incident's key, copied exactly")
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"]
    global_impact: bool
    priority: bool
    rationale: str = Field(description="One sentence")


class TriageReport(BaseModel):
    decisions: list[TriageDecision]


class ImpactDecision(BaseModel):
    key: str = Field(description="The incident's key, copied exactly")
    corroborated: bool = Field(description="Recent independent reports corroborate customer impact")
    global_evidence: bool = Field(description="Independent results support multi-region or worldwide impact")
    confidence: Literal["unavailable", "low", "medium", "high"]
    summary: str = Field(description="One factual sentence describing the independent evidence or its absence")
    regions: list[str] = Field(description="Named affected regions or countries supported by the results")
    sources: list[str] = Field(description="URLs of relevant search results only")


class ImpactReport(BaseModel):
    decisions: list[ImpactDecision]


class EmailCopy(BaseModel):
    subject: str = Field(description="Under 90 characters, naming the services and severity")
    headline: str = Field(description="One factual sentence for the top of the email")


def _confirmed(state: MonitorState) -> list[dict]:
    return [report for report in state.get("reports", []) if report["is_service_incident"]]


def _needs_verification(state: MonitorState) -> bool:
    settings = get_settings().verification
    return settings.enabled and any(
        decision["severity"] in settings.severities for decision in state.get("triage", [])
    )


def _required_next(state: MonitorState) -> NextStep:
    if state["mode"] == "incident_alert":
        if "reports" not in state:
            return "status_watcher"
        if not _confirmed(state):
            return "finish"
        if "triage" not in state:
            return "triage"
        if _needs_verification(state) and "verification" not in state:
            return "impact_verifier"
        return "notifier" if "emails" not in state else "finish"
    if "report_markdown" not in state:
        return "postmortem_analyst"
    return "notifier" if "emails" not in state else "finish"


def _progress(state: MonitorState) -> str:
    lines = [f"Mode: {state['mode']}"]
    if state["mode"] == "incident_alert":
        lines.append(f"New or escalated status-page entries detected: {len(state.get('candidates', []))}")
        if "reports" in state:
            lines.append(f"status_watcher: done, {len(_confirmed(state))} of {len(state['reports'])} confirmed as incidents")
        else:
            lines.append("status_watcher: not run yet")
        if "triage" in state:
            priority = sum(decision["priority"] for decision in state["triage"])
            lines.append(f"triage: done, {priority} priority or global incident(s)")
        else:
            lines.append("triage: not run yet")
        if "verification" in state:
            corroborated = sum(item["corroborated"] for item in state["verification"])
            lines.append(f"impact_verifier: done, {corroborated} incident(s) independently corroborated")
        elif _needs_verification(state):
            lines.append("impact_verifier: required for SEV1/SEV2, not run yet")
    else:
        lines.append(
            f"postmortem_analyst: done, report at {state['report_path']}"
            if "report_markdown" in state
            else "postmortem_analyst: not run yet"
        )
    lines.append(f"notifier: done, {len(state['emails'])} email(s)" if "emails" in state else "notifier: not run yet")
    return "\n".join(lines)


async def orchestrator(
    state: MonitorState,
) -> Command[
    Literal["status_watcher", "triage", "impact_verifier", "postmortem_analyst", "notifier", "__end__"]
]:
    turns = state.get("turns", 0) + 1
    required = _required_next(state)
    if turns > MAX_ORCHESTRATOR_TURNS:
        choice, reason = "finish", "Turn limit reached"
    else:
        try:
            decision = await get_llm().with_structured_output(Handoff).ainvoke(
                [SystemMessage(content=ORCHESTRATOR_PROMPT), HumanMessage(content=_progress(state))]
            )
            choice, reason = decision.next_agent, decision.reason
        except Exception as exc:
            choice, reason = required, f"Model unavailable ({type(exc).__name__}), following the standard workflow"
        if choice != required:
            store.log("Orchestrator", "guardrail", f"Model chose {choice} ({reason}), but {required} must run next")
            choice, reason = required, "Required next step in the workflow"
    store.log("Orchestrator", "handoff", f"Handing off to {choice}: {reason}")
    return Command(
        goto=END if choice == "finish" else choice,
        update={"turns": turns, "handoffs": [f"orchestrator -> {choice}"]},
    )


async def status_watcher(state: MonitorState) -> Command[Literal["orchestrator"]]:
    candidates = state["candidates"]
    result = await get_llm().with_structured_output(WatchReport).ainvoke(
        [SystemMessage(content=WATCHER_PROMPT), HumanMessage(content=json.dumps(candidates, indent=1))]
    )
    by_key = {report.key: report.model_dump() for report in result.reports}
    reports = []
    for candidate in candidates:
        report = by_key.get(candidate["key"]) or {
            "key": candidate["key"],
            "is_service_incident": True,
            "summary": (candidate["updates"] or [candidate["title"]])[0],
            "affected": candidate["components"],
        }
        reports.append(report)
    store.save_watch_reports(reports)
    confirmed = [report for report in reports if report["is_service_incident"]]
    store.log(
        "Status Watcher",
        "agent",
        f"Confirmed {len(confirmed)} of {len(reports)} new entries as incidents; handing back to the orchestrator",
    )
    return Command(goto="orchestrator", update={"reports": reports, "handoffs": ["status_watcher -> orchestrator"]})


async def triage(state: MonitorState) -> Command[Literal["orchestrator"]]:
    candidates = {candidate["key"]: candidate for candidate in state["candidates"]}
    service_status = store.services()
    items = []
    for report in _confirmed(state):
        candidate = candidates[report["key"]]
        service = service_status.get(candidate["service"], {})
        items.append(
            {
                **report,
                "service": candidate["service"],
                "title": candidate["title"],
                "kind": candidate["kind"],
                "vendor_impact": candidate["impact"],
                "status": candidate["status"],
                "components_affected": len(candidate["components"]),
                "vendor_page_status": f"{service.get('indicator')}: {service.get('description')}",
                "degraded_components_on_page": len(service.get("degraded_components", [])),
            }
        )
    result = await get_llm().with_structured_output(TriageReport).ainvoke(
        [SystemMessage(content=TRIAGE_PROMPT), HumanMessage(content=json.dumps(items, indent=1))]
    )
    by_key = {decision.key: decision.model_dump() for decision in result.decisions}
    decisions = []
    for item in items:
        decision = by_key.get(item["key"]) or {
            "key": item["key"],
            "severity": "SEV1" if item["vendor_impact"] == "critical" else "SEV3",
            "global_impact": False,
            "priority": item["vendor_impact"] == "critical",
            "rationale": "Triage model gave no decision; rated from the vendor's impact level",
        }
        decision["priority"] = bool(decision["priority"] or decision["global_impact"] or decision["severity"] == "SEV1")
        decisions.append(decision)
    store.save_triage(decisions)
    priority = [decision for decision in decisions if decision["priority"]]
    store.log(
        "Triage",
        "agent",
        f"Triaged {len(decisions)} incident(s), {len(priority)} priority; handing back to the orchestrator",
    )
    return Command(goto="orchestrator", update={"triage": decisions, "handoffs": ["triage -> orchestrator"]})


async def impact_verifier(state: MonitorState) -> Command[Literal["orchestrator"]]:
    """Corroborate preliminary SEV1/SEV2 incidents with recent Reddit and web evidence."""
    settings = get_settings().verification
    candidates = {candidate["key"]: candidate for candidate in state["candidates"]}
    reports = {report["key"]: report for report in state["reports"]}
    targets = [
        decision for decision in state["triage"] if decision["severity"] in settings.severities
    ]
    searches = await asyncio.gather(
        *(
            search_incident_evidence(
                candidates[decision["key"]]["service"],
                candidates[decision["key"]]["title"],
                settings.results_per_query,
            )
            for decision in targets
        )
    )
    payload = []
    evidence_by_key = {}
    for decision, evidence in zip(targets, searches):
        candidate = candidates[decision["key"]]
        evidence_by_key[decision["key"]] = evidence
        payload.append(
            {
                "key": decision["key"],
                "vendor_incident": {
                    "service": candidate["service"],
                    "title": candidate["title"],
                    "status": candidate["status"],
                    "vendor_impact": candidate["impact"],
                    "summary": reports[decision["key"]]["summary"],
                    "preliminary_triage": decision,
                },
                "search_evidence": evidence,
            }
        )

    try:
        result = await get_llm().with_structured_output(ImpactReport).ainvoke(
            [
                SystemMessage(content=IMPACT_VERIFIER_PROMPT),
                HumanMessage(content=json.dumps(payload, indent=1)),
            ]
        )
        by_key = {decision.key: decision.model_dump() for decision in result.decisions}
    except Exception as exc:
        by_key = {}
        store.log("Impact Verifier", "error", f"LLM judge unavailable: {type(exc).__name__}: {exc}")

    verifications = []
    updated_triage = [dict(decision) for decision in state["triage"]]
    triage_by_key = {decision["key"]: decision for decision in updated_triage}
    for target in targets:
        evidence = evidence_by_key[target["key"]]
        allowed_urls = {
            item["link"] for item in evidence["results"] if item.get("link")
        }
        verification = by_key.get(target["key"]) or {
            "key": target["key"],
            "corroborated": False,
            "global_evidence": False,
            "confidence": "unavailable" if evidence["errors"] else "low",
            "summary": (
                "; ".join(evidence["errors"])
                if evidence["errors"]
                else "Recent search results were inconclusive."
            ),
            "regions": [],
            "sources": [],
        }
        verification["sources"] = [
            url for url in verification["sources"] if url in allowed_urls
        ][:5]
        if verification["confidence"] == "unavailable" and not evidence["errors"]:
            verification["confidence"] = "low"
            if not verification["sources"]:
                verification["summary"] = (
                    "Recent Serper results did not provide relevant independent corroboration."
                )
        verification["corroborated"] = bool(
            verification["corroborated"]
            and verification["confidence"] != "unavailable"
            and verification["sources"]
        )
        # Search may strengthen preliminary triage, but never downgrade vendor-confirmed global impact.
        independently_global = bool(
            verification["global_evidence"]
            and verification["confidence"] in {"medium", "high"}
            and verification["sources"]
        )
        verification["global_evidence"] = independently_global
        decision = triage_by_key[target["key"]]
        decision["global_impact"] = bool(decision["global_impact"] or independently_global)
        decision["priority"] = bool(
            decision["global_impact"] or decision["severity"] == "SEV1"
        )
        decision["rationale"] += (
            f" External verification ({verification['confidence']}): {verification['summary']}"
        )
        decision["verification"] = verification
        verifications.append(verification)

    store.save_triage(updated_triage)
    store.save_verifications(verifications)
    corroborated = sum(item["corroborated"] for item in verifications)
    global_count = sum(item["global_evidence"] for item in verifications)
    store.log(
        "Impact Verifier",
        "agent",
        f"Checked {len(verifications)} SEV1/SEV2 incident(s) through Serper; "
        f"{corroborated} corroborated, {global_count} with global evidence; "
        "handing back to the orchestrator",
    )
    return Command(
        goto="orchestrator",
        update={
            "triage": updated_triage,
            "verification": verifications,
            "handoffs": ["impact_verifier -> orchestrator"],
        },
    )


def _incident_items(state: MonitorState) -> list[dict]:
    candidates = {candidate["key"]: candidate for candidate in state["candidates"]}
    reports = {report["key"]: report for report in state["reports"]}
    items = []
    for decision in state["triage"]:
        candidate, report = candidates[decision["key"]], reports[decision["key"]]
        items.append({**candidate, **report, **decision})
    order = {"SEV1": 0, "SEV2": 1, "SEV3": 2, "SEV4": 3}
    return sorted(items, key=lambda item: (not item["priority"], order[item["severity"]]))


def _incident_html(item: dict) -> str:
    colour = SEVERITY_COLOURS[item["severity"]]
    badge_text = "#ffffff" if item["severity"] in {"SEV1", "SEV2"} else "#172033"
    tags = f"{item['severity']}{' · GLOBAL IMPACT' if item['global_impact'] else ''}"
    if item["kind"] == "escalated":
        tags += " · ESCALATED"
    affected = ", ".join(item["affected"][:10]) or "Not stated"
    verification = item.get("verification")
    verification_html = ""
    if verification:
        links = " · ".join(
            f'<a href="{escape(url)}">source {index}</a>'
            for index, url in enumerate(verification["sources"], 1)
        )
        verification_html = (
            f'<div style="font-family:Arial,sans-serif;margin:14px 0 0;padding:11px 13px;'
            f'font-size:12px;line-height:1.55;color:#475569;background:#f8fafc;border:1px solid #e2e8f0">'
            f"<b>External verification ({escape(verification['confidence'])}):</b> "
            f"{escape(verification['summary'])}"
            f"{'<br><b>Evidence:</b> ' + links if links else ''}</div>"
        )
    return f"""<div style="border:1px solid #dbe3ee;border-left:6px solid {colour};border-radius:8px;padding:17px 18px;margin:14px 0;background:#ffffff">
<div style="font-family:Arial,sans-serif;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.4px">
  <span style="display:inline-block;background:{colour};color:{badge_text};font-weight:bold;padding:4px 8px;border-radius:4px;margin-right:7px">{escape(tags)}</span>
  {escape(item['service'])} &middot; {escape(item['status'])}
</div>
<h3 style="font-family:Arial,sans-serif;font-size:18px;line-height:1.35;color:#0f172a;margin:11px 0 8px">{escape(item['title'])}</h3>
<p style="font-family:Arial,sans-serif;font-size:14px;line-height:1.55;color:#334155;margin:0 0 13px">{escape(item['summary'])}</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:12px;color:#475569">
  <tr><td style="width:82px;padding:5px 8px 5px 0;font-weight:bold;vertical-align:top">Affected</td><td style="padding:5px 0">{escape(affected)}</td></tr>
  <tr><td style="width:82px;padding:5px 8px 5px 0;font-weight:bold;vertical-align:top">Triage</td><td style="padding:5px 0">{escape(item['rationale'])}</td></tr>
</table>
{verification_html}
<div style="margin-top:16px">
  <a href="{escape(item['link'])}" style="display:inline-block;background:#155eef;color:#ffffff;text-decoration:none;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;padding:9px 14px;border-radius:5px">View incident on {escape(item['service'])}</a>
</div>
</div>"""


def _incident_text(item: dict) -> str:
    verification = item.get("verification")
    verification_text = (
        f"External verification ({verification['confidence']}): {verification['summary']}\n"
        + "".join(f"Evidence: {url}\n" for url in verification["sources"])
        if verification
        else ""
    )
    return (
        f"[{item['severity']}{' GLOBAL' if item['global_impact'] else ''}] {item['service']}: {item['title']}\n"
        f"Status: {item['status']}\n{item['summary']}\nTriage: {item['rationale']}\n"
        f"{verification_text}Link: {item['link']}\n"
    )


async def _email_copy(items: list[dict]) -> EmailCopy:
    brief = [
        {key: item[key] for key in ("service", "title", "severity", "global_impact", "status", "summary")}
        for item in items
    ]
    try:
        return await get_llm().with_structured_output(EmailCopy).ainvoke(
            [SystemMessage(content=NOTIFIER_PROMPT), HumanMessage(content=json.dumps(brief, indent=1))]
        )
    except Exception:
        first = items[0]
        return EmailCopy(
            subject=f"{first['severity']} {first['service']}: {first['title']}"[:90],
            headline=f"{len(items)} SaaS incident(s) reported on vendor status pages.",
        )


def _wrap_email(headline: str, body: str) -> str:
    return shell(headline, body)


async def _notify_incidents(state: MonitorState) -> list[dict]:
    items = _incident_items(state)
    dry_run = state.get("dry_run", False)
    emails = []
    for item in [item for item in items if item["priority"]]:
        copy = await _email_copy([item])
        prefix = "[PRIORITY][GLOBAL]" if item["global_impact"] else "[PRIORITY]"
        subject = f"{prefix} {copy.subject}"
        sent = send_email(
            "priority_incident",
            subject,
            _wrap_email(copy.headline, _incident_html(item)),
            f"{copy.headline}\n\n{_incident_text(item)}",
            recipients(priority=True),
            priority=True,
            dry_run=dry_run,
        )
        if sent:
            store.mark_notified([item["key"]])
        emails.append({"subject": subject, "priority": True, "sent": sent})
    routine = [item for item in items if not item["priority"]]
    if routine:
        copy = await _email_copy(routine)
        subject = f"[SRE Monitor] {copy.subject}"
        sent = send_email(
            "incident",
            subject,
            _wrap_email(copy.headline, "".join(_incident_html(item) for item in routine)),
            copy.headline + "\n\n" + "\n".join(_incident_text(item) for item in routine),
            recipients(),
            dry_run=dry_run,
        )
        if sent:
            store.mark_notified([item["key"] for item in routine])
        emails.append({"subject": subject, "priority": False, "sent": sent})
    for item in items:
        if item["severity"] not in PUSH_SEVERITIES:
            continue
        title = f"[{item['severity']}] {item['service']}: {item['title']}"[:250]
        sent = send_push(title, f"{item['summary']}\n\nStatus: {item['status']}", item["link"], item["severity"], dry_run)
        emails.append({"subject": title, "priority": item["severity"] == "SEV1", "sent": sent})
    return emails


async def _notify_daily_review(state: MonitorState) -> list[dict]:
    markdown = state["report_markdown"]
    report_name = state["report_path"].rsplit("/", 1)[-1]
    try:
        copy = await get_llm().with_structured_output(EmailCopy).ainvoke(
            [
                SystemMessage(
                    content=NOTIFIER_PROMPT + DAILY_REVIEW_EMAIL_NOTE
                ),
                HumanMessage(content=markdown[:4000]),
            ]
        )
    except Exception:
        copy = EmailCopy(subject="Daily SaaS incident and postmortem review", headline="The last 24 hours of SaaS incidents.")
    subject = f"[SRE Monitor] Daily review: {copy.subject}"
    body = (
        markdown_to_email_html(markdown)
        + f'<div style="font-family:Arial,sans-serif;font-size:12px;color:#64748b;background:#f8fafc;'
        f'border:1px solid #e2e8f0;padding:10px 12px;margin-top:20px">'
        f'The complete Markdown report is attached as <b>{escape(report_name)}</b>.</div>'
    )
    sent = send_email(
        "daily_review",
        subject,
        _wrap_email(copy.headline, body),
        f"{copy.headline}\n\n{markdown}",
        recipients(),
        attachments=[(report_name, markdown.encode(), "text/markdown")],
        dry_run=state.get("dry_run", False),
    )
    return [{"subject": subject, "priority": False, "sent": sent}]


async def notifier(state: MonitorState) -> Command[Literal["orchestrator"]]:
    if state["mode"] == "incident_alert":
        emails = await _notify_incidents(state)
    else:
        emails = await _notify_daily_review(state)
    succeeded = sum(notification["sent"] for notification in emails)
    failed = len(emails) - succeeded
    store.log(
        "Notifier",
        "agent",
        f"Processed {len(emails)} notification(s): {succeeded} succeeded, {failed} failed; "
        "handing back to the orchestrator",
    )
    return Command(goto="orchestrator", update={"emails": emails, "handoffs": ["notifier -> orchestrator"]})


@tool
def read_incident_page(url: str) -> str:
    """Read the text of a status-page incident page, or a postmortem page it links to.
    Returns up to about 6000 characters, starting near any postmortem or root-cause section."""
    return read_page_text(url)


async def postmortem_analyst(state: MonitorState) -> Command[Literal["orchestrator"]]:
    settings = get_settings()
    hours = settings.monitor.lookback_hours
    incidents = store.incidents_since(hours)
    order = {"SEV1": 0, "SEV2": 1, "SEV3": 2, "SEV4": 3, None: 4}
    incidents.sort(key=lambda item: (not item["priority"], order.get(item["severity"], 4)))
    selected = incidents[: settings.monitor.max_postmortem_incidents]

    now = datetime.now().astimezone()
    title = f"# SaaS incident and postmortem review, {now:%Y-%m-%d}"
    meta = (
        f"Window: last {hours} hours, generated {now:%Y-%m-%d %H:%M %Z} by {model_label()}. "
        f"{len(incidents)} incident(s) reported; {len(selected)} reviewed."
    )
    if selected:
        payload = [
            {
                **{
                    key: incident[key]
                    for key in ("service", "name", "status", "impact", "link", "created_at", "resolved_at", "summary", "updates")
                },
                "severity": incident["severity"] or "not triaged",
                "global_impact": "not triaged" if incident["global_impact"] is None else incident["global_impact"],
            }
            for incident in selected
        ]
        agent = create_agent(model=get_llm(), tools=[read_incident_page], system_prompt=POSTMORTEM_PROMPT)
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=json.dumps(payload, indent=1))]},
            config={"recursion_limit": 4 * len(selected) + 20},
        )
        body = result["messages"][-1].text
    else:
        body = "No incidents were reported on the monitored status pages in this window."

    markdown = f"{title}\n\n{meta}\n\n{body.strip()}\n"
    REPORTS_DIR.mkdir(exist_ok=True)
    path = REPORTS_DIR / f"postmortem-{now:%Y-%m-%d-%H%M}.md"
    path.write_text(markdown)
    store.log(
        "Postmortem Analyst",
        "agent",
        f"Reviewed {len(selected)} incident(s), wrote reports/{path.name}; handing back to the orchestrator",
    )
    return Command(
        goto="orchestrator",
        update={
            "report_markdown": markdown,
            "report_path": str(path),
            "handoffs": ["postmortem_analyst -> orchestrator"],
        },
    )


def build_graph():
    graph = StateGraph(MonitorState)
    graph.add_node("orchestrator", orchestrator)
    graph.add_node("status_watcher", status_watcher)
    graph.add_node("triage", triage)
    graph.add_node("impact_verifier", impact_verifier)
    graph.add_node("notifier", notifier)
    graph.add_node("postmortem_analyst", postmortem_analyst)
    graph.add_edge(START, "orchestrator")
    return graph.compile()


team = build_graph()


@traceable(name="SRE Monitor - Incident Alert", run_type="chain")
async def run_incident_alert(candidates: list[dict], dry_run: bool = False) -> MonitorState:
    store.log("Orchestrator", "trace", f"Incident alert started for {len(candidates)} new or escalated entries")
    return await team.ainvoke(
        {"mode": "incident_alert", "dry_run": dry_run, "candidates": candidates}, config={"recursion_limit": 30}
    )


@traceable(name="SRE Monitor - Daily Review", run_type="chain")
async def run_daily_review(dry_run: bool = False) -> MonitorState:
    store.log("Orchestrator", "trace", "Daily postmortem review started")
    return await team.ainvoke({"mode": "daily_review", "dry_run": dry_run}, config={"recursion_limit": 30})
