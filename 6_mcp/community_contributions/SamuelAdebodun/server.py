"""
MCP server: Kubernetes health views over mock JSON (no live cluster).

Run: python server.py   (stdio transport)
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

_ROOT = Path(__file__).resolve().parent
_DATA_FILE = _ROOT / "sample_cluster.json"

mcp = FastMCP("k8s_health_mcp")


def _load_snapshot() -> dict:
    if not _DATA_FILE.is_file():
        return {"error": f"Missing data file: {_DATA_FILE}"}
    with open(_DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


@mcp.tool()
def cluster_overview() -> str:
    """High-level mock cluster view: name, version, nodes, pod counts by phase/issue."""
    d = _load_snapshot()
    if "error" in d:
        return d["error"]
    lines = [
        f"Cluster: {d.get('cluster', '?')}",
        f"API/Kubelet version (mock): {d.get('version', '?')}",
        "",
        "Nodes:",
    ]
    for n in d.get("nodes", []):
        status = "Ready" if n.get("ready") else f"NOT Ready ({n.get('condition', 'unknown')})"
        lines.append(f"  - {n.get('name')}: {status}")
    lines.append("")
    lines.append("Namespaces (pod roll-up):")
    for ns, data in d.get("namespaces", {}).items():
        pods = data.get("pods", [])
        bad = sum(1 for p in pods if p.get("issue"))
        lines.append(f"  - {ns}: {len(pods)} pod(s), {bad} with reported issues")
    return "\n".join(lines)


@mcp.tool()
def namespace_health(namespace: str) -> str:
    """Pods and deployments in one mock namespace."""
    d = _load_snapshot()
    if "error" in d:
        return d["error"]
    ns = (namespace or "").strip()
    block = d.get("namespaces", {}).get(ns)
    if not block:
        known = ", ".join(sorted(d.get("namespaces", {}).keys())) or "(none)"
        return f"Namespace '{ns}' not in mock data. Known: {known}"
    lines = [f"Namespace: {ns}", "", "Pods:"]
    for p in block.get("pods", []):
        issue = p.get("issue") or "ok"
        lines.append(
            f"  - {p['name']}: phase={p.get('phase')} ready={p.get('ready')} "
            f"restarts={p.get('restarts')} issue={issue} workload={p.get('workload')}"
        )
    lines.extend(["", "Deployments:"])
    for dep in block.get("deployments", []):
        lines.append(
            f"  - {dep['name']}: desired={dep.get('desired')} ready={dep.get('ready')} "
            f"available={dep.get('available')}"
        )
    return "\n".join(lines)


@mcp.tool()
def workload_health(namespace: str, workload: str) -> str:
    """Filter mock pods for a workload name within a namespace."""
    d = _load_snapshot()
    if "error" in d:
        return d["error"]
    ns = (namespace or "").strip()
    name = (workload or "").strip()
    block = d.get("namespaces", {}).get(ns)
    if not block:
        return f"Unknown namespace '{ns}'"
    hits = [p for p in block.get("pods", []) if p.get("workload") == name]
    if not hits:
        all_w = sorted({p.get("workload") for p in block.get("pods", [])})
        return f"No pods for workload '{name}' in {ns}. Workloads here: {all_w}"
    lines = [f"Workload {name} ({ns})", ""]
    for p in hits:
        lines.append(
            f"- {p['name']}: {p.get('phase')} restarts={p.get('restarts')} issue={p.get('issue') or 'none'}"
        )
    return "\n".join(lines)


@mcp.tool()
def incident_summary(namespace: str) -> str:
    """Short mock triage bullets for on-call style handoff."""
    d = _load_snapshot()
    if "error" in d:
        return d["error"]
    ns = (namespace or "").strip()
    overview = cluster_overview()
    ns_health = namespace_health(ns)
    lines = [
        f"Triage (mock data) — namespace `{ns}`",
        "",
        "### Cluster signals",
        overview.split("Namespaces", 1)[0].strip(),
        "",
        "### Namespace detail",
        ns_health,
        "",
        "### Suggested next checks",
        "- Compare with latest deploy / config change window.",
        "- Check node conditions if pods are Pending or evicted.",
        "- For CrashLoopBackOff: logs + previous container exit reason.",
        "- Fetch runbook resource runbook://k8s/common-issues for patterns.",
    ]
    return "\n".join(lines)


@mcp.resource("runbook://k8s/common-issues")
def k8s_common_issues_runbook() -> str:
    """Markdown hints for mock triage; not a substitute for your internal runbooks."""
    return """# Kubernetes — common issues (cheat sheet)

## CrashLoopBackOff
- `kubectl logs <pod> -n <ns> --previous`
- Check OOMKilled, missing env, bad liveness probe timing.

## ImagePullBackOff / ErrImagePull
- Image name/tag, registry auth, imagePullSecrets.

## Pending pods
- `kubectl describe pod` — Events (Insufficient cpu, PVC bind, tolerations).
- Node taints / topology spreads.

## DiskPressure (node)
- Free disk, eviction thresholds, log volume growth.

## Deployment not fully available
- Rolling update stuck — maxUnavailable, readiness probe, failed new ReplicaSet.

_Mock MCP only: wire real kubectl in a fork for production use._
"""


if __name__ == "__main__":
    mcp.run(transport="stdio")
