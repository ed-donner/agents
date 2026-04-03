import json
import os
from datetime import datetime
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Applications")

APPLICATIONS_FILE = "applications.json"

def load_applications() -> list:
    if not os.path.exists(APPLICATIONS_FILE):
        return []
    with open(APPLICATIONS_FILE, "r") as f:
        return json.load(f)

def save_applications(applications: list):
    with open(APPLICATIONS_FILE, "w") as f:
        json.dump(applications, f, indent=2)

@mcp.tool()
def add_application(company: str, role: str, job_url: str, status: str = "Applied") -> str:
    """Save a new job application to the tracker."""
    applications = load_applications()
    application = {
        "id": len(applications) + 1,
        "company": company,
        "role": role,
        "job_url": job_url,
        "status": status,
        "date_applied": datetime.now().strftime("%Y-%m-%d"),
    }
    applications.append(application)
    save_applications(applications)
    return f"Application saved: {role} at {company} (ID: {application['id']})"

@mcp.tool()
def get_applications() -> str:
    """Retrieve all tracked job applications."""
    applications = load_applications()
    if not applications:
        return "No applications tracked yet."
    return json.dumps(applications, indent=2)

@mcp.tool()
def update_application_status(application_id: int, status: str) -> str:
    """Update the status of an existing application (e.g. Interviewing, Rejected, Offer)."""
    applications = load_applications()
    for app in applications:
        if app["id"] == application_id:
            app["status"] = status
            save_applications(applications)
            return f"Application {application_id} updated to: {status}"
    return f"Application with ID {application_id} not found."

if __name__ == "__main__":
    mcp.run(transport="stdio")
