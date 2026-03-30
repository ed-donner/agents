import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("report-storage")

STORAGE_DIR = Path(os.environ.get("REPORT_STORAGE_DIR", "./storage/reports"))
INDEX_FILE = STORAGE_DIR / "index.json"

def _load_index():
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {}

def _save_index(index):
    INDEX_FILE.write_text(json.dumps(index, indent=2))

def _repo_key(repo_url):
    return hashlib.md5(repo_url.strip().lower().encode()).hexdigest()[:12]


@mcp.tool()
def save_report(
    repo_url,
    report_path,
    summary,
    health_score = None
):
    """Index a written report for history tracking and retrieval."""
    try:
        if not Path(report_path).exists():
            return {"success": False, "error": f"Report file not found: '{report_path}'"}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = f"{_repo_key(repo_url)}_{timestamp}"

        index = _load_index()
        if repo_url not in index:
            index[repo_url] = []

        index[repo_url].append({
            "report_id": report_id,
            "timestamp": timestamp,
            "summary": summary[:300],
            "health_score": health_score,
            "file": report_path
        })
        _save_index(index)

        return {"success": True, "report_id": report_id, "file_path": report_path}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_report(report_id):
    """Retrieve a specific report by its report ID."""
    try:
        report_file = STORAGE_DIR / f"{report_id}.md"
        if not report_file.exists():
            return {"success": False, "error": f"Report '{report_id}' not found."}

        content = report_file.read_text(encoding="utf-8")
        index = _load_index()
        metadata = None
        for reports in index.values():
            for r in reports:
                if r["report_id"] == report_id:
                    metadata = r
                    break

        return {"success": True, "report_id": report_id, "content": content, "metadata": metadata}

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_reports(repo_url):
    """List all past review reports for a repository."""
    try:
        index = _load_index()
        reports = index.get(repo_url, [])
        return {
            "success": True,
            "repo_url": repo_url,
            "total": len(reports),
            "reports": sorted(reports, key=lambda r: r["timestamp"], reverse=True)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def diff_reports(report_id_1, report_id_2):
    """Compare two reports and return a summary of what changed between them."""
    try:
        r1 = get_report(report_id_1)
        r2 = get_report(report_id_2)

        if not r1["success"]:
            return {"success": False, "error": f"Report 1 not found: {report_id_1}"}
        if not r2["success"]:
            return {"success": False, "error": f"Report 2 not found: {report_id_2}"}

        m1 = r1.get("metadata") or {}
        m2 = r2.get("metadata") or {}
        score1 = m1.get("health_score")
        score2 = m2.get("health_score")

        score_change = None
        score_direction = "unchanged"
        if score1 is not None and score2 is not None:
            score_change = round(score2 - score1, 1)
            score_direction = (
                "improved" if score_change > 0
                else "declined" if score_change < 0
                else "unchanged"
            )

        return {
            "success": True,
            "report_id_1": report_id_1,
            "report_id_2": report_id_2,
            "timestamp_1": m1.get("timestamp", "unknown"),
            "timestamp_2": m2.get("timestamp", "unknown"),
            "health_score_1": score1,
            "health_score_2": score2,
            "score_change": score_change,
            "score_direction": score_direction,
            "summary_1": m1.get("summary", ""),
            "summary_2": m2.get("summary", "")
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    mcp.run()