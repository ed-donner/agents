#!/usr/bin/env python
import os
import warnings
from datetime import datetime

from incident_postmortem.crew import IncidentPostmortem

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

os.makedirs("output", exist_ok=True)

# Paste-friendly sample incident; replace with your own notes for a real run.
INCIDENT_NOTES = """
2025-03-18 09:12 — Pager: checkout-api error rate > 5% in us-east-1.
09:18 — On-call restarted two unhealthy pods; errors dipped briefly then returned.
09:35 — Found bad deploy: config flag PAYMENTS_RETRY_MAX set to 0 in prod by mistake.
09:50 — Rolled back to previous release; error rate normalized within minutes.
10:05 — Incident closed. Est. ~12k failed checkouts over 43 minutes; no data loss.
Follow-up ideas: add deploy-time validation for critical flags; canary still 10% only.
"""


def run():
    """
    Run the postmortem crew. Writes output/postmortem.md (see tasks.yaml output_file).
    """
    report_date = datetime.now().strftime("%Y-%m-%d")
    inputs = {
        "incident_notes": INCIDENT_NOTES.strip(),
        "service_name": "checkout-api",
        "severity": "SEV-2",
        "report_date": report_date,
    }

    try:
        result = IncidentPostmortem().crew().kickoff(inputs=inputs)
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}") from e


if __name__ == "__main__":
    run()
