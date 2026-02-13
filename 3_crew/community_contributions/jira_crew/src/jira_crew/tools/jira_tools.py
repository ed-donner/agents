"""CrewAI tools for Jira: epics, sprints, boards (MCP-style API)."""
import json
import base64
import os
from typing import Optional
from crewai.tools import tool
import requests

def _get_jira_config():
    base_url = (os.getenv("JIRA_BASE_URL") or "").strip().rstrip("/")
    email = (os.getenv("JIRA_EMAIL") or "").strip()
    token = (os.getenv("JIRA_API_TOKEN") or "").strip()
    if not base_url or "your-domain" in base_url or not email or not token:
        return None, None, None
    return base_url, email, token

def _headers():
    base_url, email, token = _get_jira_config()
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if base_url and email and token:
        creds = base64.b64encode(f"{email}:{token}".encode()).decode()
        h["Authorization"] = f"Basic {creds}"
    return h

# Placeholder project keys the agent might use; we replace with JIRA_PROJECT_KEY when set
_DEFAULT_PROJECT_PLACEHOLDERS = frozenset({"PROJ", "EXAMPLE", "MYPROJECT", "PROJECT", "KEY"})


@tool("List Jira epics")
def list_epics(project_key: Optional[str] = None, **kwargs) -> str:
    """List all epics, optionally filtered by project key (e.g. SCRUM). Use the real project key from the user's Jira; if unsure, omit project_key or set JIRA_PROJECT_KEY in .env."""
    base_url, _, _ = _get_jira_config()
    if not base_url:
        return "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env to use this tool."
    key = (project_key or "").strip().upper()
    if not key or key in _DEFAULT_PROJECT_PLACEHOLDERS:
        key = (os.getenv("JIRA_PROJECT_KEY") or "").strip().upper()
    # Use new JQL search API (old /rest/api/3/search was removed by Atlassian)
    url = f"{base_url}/rest/api/3/search/jql"
    jql = "issuetype = Epic"
    if key:
        jql += f" AND project = {key}"
    try:
        r = requests.post(
            url,
            headers=_headers(),
            json={"jql": jql, "fields": ["summary", "description", "status", "assignee", "created"], "maxResults": 50},
            timeout=30,
        )
        if r.status_code != 200:
            return f"Jira API error: {r.status_code} - {r.text[:200]}"
        data = r.json()
        issues = data.get("issues", [])
        if not issues:
            return "No epics found."
        lines = [f"- {i.get('key')}: {i.get('fields', {}).get('summary', 'N/A')} (Status: {i.get('fields', {}).get('status', {}).get('name', 'N/A')})" for i in issues]
        return "Epics:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing epics: {e}"

def _fetch_boards(base_url: str, project_key: Optional[str] = None):
    """GET /rest/agile/1.0/board with optional projectKeyOrId and pagination."""
    url = f"{base_url}/rest/agile/1.0/board"
    params = {"maxResults": 50}
    if project_key:
        params["projectKeyOrId"] = project_key.strip().upper()
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    if r.status_code != 200:
        return r.status_code, r.text, []
    data = r.json()
    return r.status_code, r.text, data.get("values", [])


@tool("Get Jira boards")
def list_boards(**kwargs) -> str:
    """List all Jira Agile boards. Uses JIRA_PROJECT_KEY (e.g. SCRUM) to filter by project if set; if list is empty and JIRA_BOARD_ID is set, shows that board. Takes no required arguments."""
    base_url, _, _ = _get_jira_config()
    if not base_url:
        return "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env."
    project_key = os.getenv("JIRA_PROJECT_KEY", "").strip() or None
    board_id_env = os.getenv("JIRA_BOARD_ID", "").strip()
    try:
        # Prefer project filter so SCRUM board is returned (API only returns boards user can see)
        code, text, boards = _fetch_boards(base_url, project_key)
        if code != 200:
            return f"Jira API error: {code} - {text[:200]}"
        if not boards and project_key is None:
            code2, _, boards = _fetch_boards(base_url, None)
            if code2 != 200 or not boards:
                pass  # keep boards empty
        if not boards and board_id_env:
            # Fallback: fetch single board by ID so it shows (e.g. board 1 for SCRUM)
            bid = int(board_id_env)
            r = requests.get(f"{base_url}/rest/agile/1.0/board/{bid}", headers=_headers(), timeout=30)
            if r.status_code == 200:
                boards = [r.json()]
        if not boards:
            return "No boards found. If you have a board (e.g. SCRUM board 1), set JIRA_PROJECT_KEY=SCRUM and optionally JIRA_BOARD_ID=1 in .env."
        lines = [f"- Board {b.get('id')}: {b.get('name')} (type: {b.get('type', 'N/A')})" for b in boards]
        return "Boards:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing boards: {e}"

@tool("List Jira sprints")
def list_sprints(board_id: Optional[int] = None, **kwargs) -> str:
    """List sprints for a board. If board_id is not given, uses the first board from the board list."""
    base_url, _, _ = _get_jira_config()
    if not base_url:
        return "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env."
    # Jira no longer supports GET /rest/agile/1.0/sprint; must use board-specific endpoint
    if not board_id:
        board_id_env = os.getenv("JIRA_BOARD_ID", "").strip()
        if board_id_env:
            try:
                board_id = int(board_id_env)
            except ValueError:
                board_id = None
        if not board_id:
            try:
                project_key = os.getenv("JIRA_PROJECT_KEY", "").strip() or None
                _, text, boards = _fetch_boards(base_url, project_key)
                if not boards:
                    _, _, boards = _fetch_boards(base_url, None)
                if not boards:
                    return "No boards found. Set JIRA_PROJECT_KEY=SCRUM and/or JIRA_BOARD_ID=1 in .env, or create a board in Jira."
                board_id = boards[0].get("id")
            except Exception as e:
                return f"Error fetching boards: {e}"
    url = f"{base_url}/rest/agile/1.0/board/{board_id}/sprint"
    try:
        r = requests.get(url, headers=_headers(), timeout=30)
        if r.status_code != 200:
            return f"Jira API error: {r.status_code} - {r.text[:200]}"
        data = r.json()
        sprints = data.get("values", [])
        if not sprints:
            return f"No sprints found for board {board_id}."
        lines = [f"- Sprint {s.get('id')}: {s.get('name')} (state: {s.get('state', 'N/A')})" for s in sprints]
        return "Sprints:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing sprints: {e}"

@tool("Create a Jira epic")
def create_epic(project_key: str, summary: str, description: str = "", **kwargs) -> str:
    """Create an epic in the given project. project_key is the project key (e.g. SCRUM, PROJ). If omitted, uses JIRA_PROJECT_KEY from env."""
    base_url, _, _ = _get_jira_config()
    if not base_url:
        return "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env."
    key = (project_key or os.getenv("JIRA_PROJECT_KEY") or "").strip().upper()
    if not key:
        return "Project key is required. Pass project_key (e.g. SCRUM) or set JIRA_PROJECT_KEY in .env."
    url = f"{base_url}/rest/api/3/issue"
    body = {
        "fields": {
            "project": {"key": key},
            "summary": summary,
            "issuetype": {"name": "Epic"},
        }
    }
    if description:
        body["fields"]["description"] = {"version": 1, "type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}]}
    try:
        r = requests.post(url, headers=_headers(), json=body, timeout=30)
        if r.status_code in (200, 201):
            d = r.json()
            return f"Created epic: {d.get('key')} - {summary}"
        return f"Failed to create epic: {r.status_code} - {r.text[:300]}"
    except Exception as e:
        return f"Error creating epic: {e}"

@tool("Create a Jira sprint")
def create_sprint(name: str, board_id: int, start_date: str = "", end_date: str = "", **kwargs) -> str:
    """Create a sprint on the given board. board_id is a number (e.g. 1)."""
    base_url, _, _ = _get_jira_config()
    if not base_url:
        return "Jira is not configured. Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env."
    url = f"{base_url}/rest/agile/1.0/sprint"
    payload = {"name": name, "originBoardId": int(board_id)}
    if start_date:
        payload["startDate"] = start_date
    if end_date:
        payload["endDate"] = end_date
    try:
        r = requests.post(url, headers=_headers(), json=payload, timeout=30)
        if r.status_code in (200, 201):
            return f"Created sprint: {name} on board {board_id}"
        return f"Failed to create sprint: {r.status_code} - {r.text[:300]}"
    except Exception as e:
        return f"Error creating sprint: {e}"
