"""
Dev Environment Doctor — MCP Server
Diagnoses local developer environment and reports issues.
"""

import subprocess
import os
import socket
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("dev-env-doctor")


def run(cmd: str) -> tuple[str, bool]:
    """Run a shell command, return (output, success)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output, result.returncode == 0
    except subprocess.TimeoutExpired:
        return "timed out", False
    except Exception as e:
        return str(e), False


def get_version(cmd: str) -> str:
    output, ok = run(cmd)
    if not ok or not output:
        return "not found"
    # Return first non-empty, non-proxy-noise line
    for line in output.splitlines():
        if line.strip() and "Picked up" not in line and "proxy" not in line.lower():
            return line.strip()
    return "not found"


@mcp.tool()
def check_runtime_versions() -> dict:
    """
    Check versions of common developer runtimes and tools installed on this machine.
    Returns a dict of tool names to their installed version (or 'not found').
    """
    checks = {
        "python":     "python3 --version",
        "node":       "node --version",
        "npm":        "npm --version",
        "go":         "go version",
        "java":       "java -version 2>&1 | head -1",
        "docker":     "docker --version",
        "git":        "git --version",
        "rust":       "rustc --version",
        "curl":       "curl --version | head -1",
    }

    results = {}
    for tool, cmd in checks.items():
        results[tool] = get_version(cmd)

    missing = [t for t, v in results.items() if v == "not found"]
    found   = [t for t, v in results.items() if v != "not found"]

    return {
        "versions": results,
        "found_count": len(found),
        "missing": missing,
        "summary": f"{len(found)}/{len(checks)} tools found. Missing: {', '.join(missing) if missing else 'none'}",
    }


@mcp.tool()
def check_env_vars(required_vars: list[str] = None) -> dict:
    """
    Check for the presence of common or user-specified environment variables.
    Pass a list of required_vars to validate custom variables; otherwise checks
    a default set of common dev environment variables.

    Args:
        required_vars: Optional list of env var names to check (e.g. ["DATABASE_URL", "API_KEY"])
    """
    defaults = [
        "HOME", "PATH", "SHELL",
        "VIRTUAL_ENV",           
        "GOPATH",                
        "JAVA_HOME",             
        "DATABASE_URL",        
        "OPENAI_API_KEY",        
        "ANTHROPIC_API_KEY",     
        "NODE_ENV",             
        "PORT",                  
    ]

    vars_to_check = required_vars if required_vars else defaults

    results = {}
    for var in vars_to_check:
        value = os.environ.get(var)
        if value is None:
            results[var] = {"status": "missing", "value": None}
        elif var.lower() in ("api_key", "secret", "password", "token") or "key" in var.lower():
            results[var] = {"status": "set", "value": "[REDACTED]"}
        else:
            results[var] = {"status": "set", "value": value[:80]}  # truncate long values

    missing = [v for v, d in results.items() if d["status"] == "missing"]
    present = [v for v, d in results.items() if d["status"] == "set"]

    return {
        "variables": results,
        "present_count": len(present),
        "missing": missing,
        "summary": f"{len(present)}/{len(vars_to_check)} variables set. Missing: {', '.join(missing) if missing else 'none'}",
    }


@mcp.tool()
def check_port_conflicts(ports: list[int] = None) -> dict:
    """
    Check which common developer ports are already in use on localhost.
    Optionally pass a custom list of ports to check.

    Args:
        ports: Optional list of port numbers to check. Defaults to common dev ports.
    """
    default_ports = {
        3000: "React / Node dev server",
        3001: "React alternate",
        4000: "GraphQL / misc",
        5000: "Flask / FastAPI",
        5432: "PostgreSQL",
        6379: "Redis",
        8000: "Django / FastAPI",
        8080: "HTTP alternate",
        8888: "Jupyter Notebook",
        27017: "MongoDB",
    }

    ports_to_check = (
        {p: "custom" for p in ports} if ports else default_ports
    )

    results = {}
    for port, label in ports_to_check.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.3)
        in_use = sock.connect_ex(("127.0.0.1", port)) == 0
        sock.close()
        results[port] = {
            "label": label,
            "in_use": in_use,
            "status": "IN USE" if in_use else "free",
        }

    in_use_ports = [p for p, d in results.items() if d["in_use"]]

    return {
        "ports": results,
        "conflicts": in_use_ports,
        "summary": (
            f"{len(in_use_ports)} port(s) in use: {in_use_ports}"
            if in_use_ports
            else "No port conflicts detected."
        ),
    }


@mcp.tool()
def generate_report() -> str:
    """
    Run all diagnostic checks and produce a full human-readable Dev Environment Report.
    Combines runtime versions, environment variables, and port conflicts.
    """
    runtimes = check_runtime_versions()
    env_vars  = check_env_vars()
    ports     = check_port_conflicts()

    lines = [
        "       DEV ENVIRONMENT DOCTOR — DIAGNOSTIC REPORT",
        "",
        "RUNTIME VERSIONS",
        "",
    ]

    for tool, version in runtimes["versions"].items():
        result = version if version != "not found" else "not found"
        lines.append(f"  ({result})  {tool:<12} {version}")

    lines += [
        "",
        f"  {runtimes['summary']}",
        "",
        "  ENVIRONMENT VARIABLES",
        "",
    ]

    for var, data in env_vars["variables"].items():
        val  = data["value"] or "not set"
        lines.append(f"    {var:<25} {val}")

    lines += [
        "",
        f"   {env_vars['summary']}",
        "",
        " PORT STATUS",
        "",
    ]

    for port, data in ports["ports"].items():
        lines.append(f"  {data['status']}  :{port:<6}  {data['label']}")

    lines += [
        "",
        f"   {ports['summary']}",
        "",
        "  Run individual tools for more detail or custom checks.",
    ]

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run(transport="stdio")