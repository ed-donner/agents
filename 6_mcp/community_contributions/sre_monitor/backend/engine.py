"""Runs the SRE monitor: polls the status pages on a timer and runs the daily postmortem review.

From the sre_monitor directory:

    uv run -m backend.engine              # run forever
    uv run -m backend.engine --once       # one poll, then exit
    uv run -m backend.engine --daily-now  # the 24-hour postmortem review, then exit
    add --dry-run to save emails to data/outbox instead of sending them
"""

import argparse
import asyncio
from datetime import datetime, timedelta

from . import store
from .agents import run_daily_review, run_incident_alert
from .settings import get_settings, model_label
from .sources import IMPACT_RANK, Incident, fetch_all


def _candidate(incident: Incident, kind: str) -> dict:
    return {
        "key": incident.key,
        "kind": kind,
        "service": incident.service,
        "title": incident.name,
        "status": incident.status,
        "impact": incident.impact,
        "components": incident.components[:15],
        "updates": incident.updates[:3],
        "link": incident.link,
        "created_at": store.iso(incident.created_at),
    }


async def poll_once(dry_run: bool = False) -> list[dict]:
    """Check every status page, record what changed, and alert the team about new or escalated incidents."""
    settings = get_settings()
    store.prune_services([service.name for service in settings.services])
    cutoff = store.utcnow() - timedelta(hours=settings.monitor.lookback_hours)
    candidates = []
    for snapshot in await fetch_all(settings.services):
        previous_error = store.save_service(snapshot)
        if snapshot.error:
            if snapshot.error != previous_error:
                store.log("Poller", "error", f"{snapshot.service}: {snapshot.error}")
            continue
        first_check = store.get_meta(f"seen:{snapshot.service}") is None
        for incident in snapshot.incidents:
            previous = store.upsert_incident(incident)
            if previous is None:
                recent = incident.created_at >= cutoff
                if recent and (not first_check or (settings.monitor.alert_active_on_first_run and incident.is_open)):
                    candidates.append(_candidate(incident, "new"))
            elif incident.is_open and IMPACT_RANK.get(incident.impact, 0) > IMPACT_RANK.get(previous["impact"], 0):
                candidates.append(_candidate(incident, "escalated"))
        if first_check:
            store.set_meta(f"seen:{snapshot.service}", store.iso(store.utcnow()))
    store.set_meta("last_poll", store.iso(store.utcnow()))
    if candidates:
        await run_incident_alert(candidates, dry_run)
    return candidates


async def daily_review(dry_run: bool = False) -> None:
    await poll_once(dry_run)
    await run_daily_review(dry_run)
    store.set_meta("last_daily_review", datetime.now().astimezone().date().isoformat())


def daily_review_due() -> bool:
    now = datetime.now().astimezone()
    if now.hour < get_settings().monitor.daily_review_hour:
        return False
    return store.get_meta("last_daily_review") != now.date().isoformat()


async def run_forever(dry_run: bool = False) -> None:
    interval = get_settings().monitor.poll_interval_minutes * 60
    while True:
        try:
            await poll_once(dry_run)
            if daily_review_due():
                await daily_review(dry_run)
        except Exception as exc:
            store.log("Engine", "error", f"{type(exc).__name__}: {exc}")
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="SaaS status-page monitor with an SRE agent team")
    parser.add_argument("--once", action="store_true", help="poll the status pages once and exit")
    parser.add_argument("--daily-now", action="store_true", help="run the 24-hour postmortem review now and exit")
    parser.add_argument("--dry-run", action="store_true", help="save emails to data/outbox instead of sending them")
    args = parser.parse_args()
    settings = get_settings()
    dry_run = args.dry_run or settings.email.dry_run
    print(f"SRE monitor: {len(settings.services)} status pages, every agent on {model_label()}")
    if args.daily_now:
        asyncio.run(daily_review(dry_run))
    elif args.once:
        asyncio.run(poll_once(dry_run))
    else:
        print(f"Polling every {settings.monitor.poll_interval_minutes} minutes; daily review after {settings.monitor.daily_review_hour}:00")
        asyncio.run(run_forever(dry_run))


if __name__ == "__main__":
    main()
