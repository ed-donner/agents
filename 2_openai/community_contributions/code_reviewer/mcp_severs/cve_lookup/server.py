import httpx
import os
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("cve-lookup")

NVD_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OSV_BASE = "https://api.osv.dev/v1"
TIMEOUT = 10

def _extract_cvss(metrics):
    for key in ["cvssMetricV31", "cvssMetricV30", "cvssMetricV2"]:
        metric_list = metrics.get(key, [])
        if metric_list:
            data = metric_list[0].get("cvssData", {})
            severity = (
                metric_list[0].get("baseSeverity") or
                data.get("baseSeverity", "UNKNOWN")
            )
            return severity.upper(), data.get("baseScore")
    return "UNKNOWN", None


@mcp.tool()
async def search_cve(library, version = ""):
    """Search the NVD database for CVEs related to a library or package."""
    query = f"{library} {version}".strip()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                NVD_BASE,
                params={"keywordSearch": query, "resultsPerPage": 5}
            )
            response.raise_for_status()
            data = response.json()

        results = []
        for item in data.get("vulnerabilities", []):
            cve = item.get("cve", {})
            cve_id = cve.get("id", "Unknown")
            descriptions = cve.get("descriptions", [])
            description = next(
                (d["value"] for d in descriptions if d.get("lang") == "en"),
                "No description available."
            )
            severity, score = _extract_cvss(cve.get("metrics", {}))
            results.append({
                "cve_id": cve_id,
                "description": description[:300],
                "severity": severity,
                "cvss_score": score,
                "published": cve.get("published", "")[:10],
                "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
            })

        return {"success": True, "query": query, "results": results, "total": len(results)}

    except Exception as e:
        return {"success": False, "error": str(e), "results": []}


@mcp.tool()
async def get_cve_details(cve_id):
    """Get full details for a specific CVE by its ID."""
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(
                NVD_BASE,
                params={"cveId": cve_id}
            )
            response.raise_for_status()
            data = response.json()

        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            return {"success": False, "error": f"CVE {cve_id} not found."}

        cve = vulnerabilities[0].get("cve", {})
        descriptions = cve.get("descriptions", [])
        description = next(
            (d["value"] for d in descriptions if d.get("lang") == "en"),
            "No description."
        )
        severity, score = _extract_cvss(cve.get("metrics", {}))
        references = [ref.get("url", "") for ref in cve.get("references", [])[:5]]

        return {
            "success": True,
            "cve_id": cve_id,
            "description": description,
            "severity": severity,
            "cvss_score": score,
            "published": cve.get("published", "")[:10],
            "last_modified": cve.get("lastModified", "")[:10],
            "references": references,
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def check_package_advisories(package, ecosystem, version = ""):
    """Check the OSV database for known vulnerabilities in a specific package."""
    payload = {"package": {"name": package, "ecosystem": ecosystem}}
    if version:
        payload["version"] = version

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(f"{OSV_BASE}/query", json=payload)
            response.raise_for_status()
            data = response.json()

        results = [
            {
                "id": v.get("id", ""),
                "summary": v.get("summary", "")[:200],
                "severity": v.get("database_specific", {}).get("severity", "UNKNOWN"),
                "published": v.get("published", "")[:10],
                "url": f"https://osv.dev/vulnerability/{v.get('id', '')}"
            }
            for v in data.get("vulns", [])[:10]
        ]

        return {
            "success": True,
            "package": package,
            "ecosystem": ecosystem,
            "version": version or "any",
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        return {"success": False, "error": str(e), "results": []}


if __name__ == "__main__":
    mcp.run()