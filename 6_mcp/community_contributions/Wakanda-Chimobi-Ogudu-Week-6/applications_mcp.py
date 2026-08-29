import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv(override=True)

APPLICATIONS_JSON_PATH = Path(__file__).resolve().parent / "applications.json"


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


def read_all() -> dict:
    return read_applications_store()


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
    store["applications"].append(record)
    write_applications_store(store)
    return record


mcp = FastMCP("applications")


@mcp.tool()
async def submit_application(
    opportunity_name: str,
    opportunity_url: str,
    applicant_name: str,
    applicant_email: str,
    profile_url: str,
    cover_letter: str,
    automation_channel: str = "none",
    automation_log: str = "",
) -> str:
    """Record one application"""
    record = append_application_record(
        opportunity_name=opportunity_name,
        opportunity_url=opportunity_url,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        profile_url=profile_url,
        cover_letter=cover_letter,
        automation_channel=automation_channel,
        automation_log=automation_log,
    )
    return json.dumps(
        {"application_id": record["application_id"], "status": record["status"]},
        ensure_ascii=False,
    )


@mcp.tool()
async def list_applications() -> str:
    """list"""
    return json.dumps(read_all(), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
