# Note: checked MCP registry — no generic logs MCP server exists; creating a lightweight one.
from mcp.server.fastmcp import FastMCP
from collections import Counter
import json

mcp = FastMCP("logs_server")

_LOGS = [
    {"ts": "2026-03-26 02:11:01", "level": "WARN",  "event": "auth_failure", "user": "root",   "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:03", "level": "WARN",  "event": "auth_failure", "user": "admin",  "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:05", "level": "WARN",  "event": "auth_failure", "user": "ubuntu", "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:07", "level": "WARN",  "event": "auth_failure", "user": "deploy", "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:09", "level": "WARN",  "event": "auth_failure", "user": "pi",     "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:11", "level": "WARN",  "event": "auth_failure", "user": "test",   "src_ip": "185.220.101.45", "service": "sshd"},
    {"ts": "2026-03-26 02:11:30", "level": "INFO",  "event": "auth_success", "user": "alice",  "src_ip": "10.0.1.5",       "service": "sshd"},
    {"ts": "2026-03-26 02:12:00", "level": "WARN",  "event": "auth_failure", "user": "root",   "src_ip": "91.241.19.223",  "service": "sshd"},
    {"ts": "2026-03-26 02:12:05", "level": "WARN",  "event": "auth_failure", "user": "root",   "src_ip": "91.241.19.223",  "service": "sshd"},
    {"ts": "2026-03-26 02:12:09", "level": "WARN",  "event": "auth_failure", "user": "root",   "src_ip": "91.241.19.223",  "service": "sshd"},
    {"ts": "2026-03-26 02:12:12", "level": "WARN",  "event": "auth_failure", "user": "root",   "src_ip": "91.241.19.223",  "service": "sshd"},
    {"ts": "2026-03-26 02:15:00", "level": "INFO",  "event": "auth_success", "user": "bob",    "src_ip": "10.0.1.12",      "service": "sshd"},
    {"ts": "2026-03-26 03:00:01", "level": "WARN",  "event": "port_scan",    "user": "",       "src_ip": "185.220.101.45", "service": "firewall"},
    {"ts": "2026-03-26 03:00:02", "level": "WARN",  "event": "port_scan",    "user": "",       "src_ip": "185.220.101.45", "service": "firewall"},
    {"ts": "2026-03-26 03:00:03", "level": "WARN",  "event": "port_scan",    "user": "",       "src_ip": "185.220.101.45", "service": "firewall"},
    {"ts": "2026-03-26 03:05:00", "level": "ERROR", "event": "priv_escalation", "user": "www-data", "src_ip": "10.0.1.5",  "service": "sudo"},
]


@mcp.tool()
async def get_recent_logs(limit: int = 50) -> str:
    """Return the most recent log entries.

    Args:
        limit: Max number of entries to return (default 50)
    """
    return json.dumps(_LOGS[-limit:], indent=2)


@mcp.tool()
async def search_logs(pattern: str, limit: int = 20) -> str:
    """Search log entries where any field matches the pattern.

    Args:
        pattern: String to match against any field value
        limit: Max number of results (default 20)
    """
    matches = [
        log for log in _LOGS
        if any(pattern.lower() in str(v).lower() for v in log.values())
    ]
    return json.dumps(matches[-limit:], indent=2)


@mcp.tool()
async def get_failed_logins(threshold: int = 3) -> str:
    """Get IPs with failed login attempts at or above the threshold.

    Args:
        threshold: Minimum failure count to include (default 3)
    """
    failures = Counter(
        log["src_ip"]
        for log in _LOGS
        if log["event"] == "auth_failure" and log["src_ip"]
    )
    flagged = {ip: count for ip, count in failures.items() if count >= threshold}
    return json.dumps({"flagged_ips": flagged, "threshold": threshold}, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")
