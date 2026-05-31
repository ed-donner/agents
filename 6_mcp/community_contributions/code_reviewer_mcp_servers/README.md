# MCP Servers

This project includes four custom MCP servers built with **FastMCP**. Each
server exposes a set of tools to a specific agent in the Code Reviewer Agent which can be in '/2_openai/community_contributions/code_reviewer' directory'. 

---

## 🔒 CVE Lookup Server
**Location:** `mcp_servers/cve_lookup/server.py`
**Used by:** Security Audit Agent

Provides structured access to public vulnerability databases so the Security
Audit Agent can verify whether a detected library or package has known CVEs,
rather than relying solely on web search results.

| Tool | Description |
|---|---|
| `search_cve` | Search the NVD database by library name and optional version |
| `get_cve_details` | Fetch full details for a specific CVE ID |
| `check_package_advisories` | Query the OSV database for a package across ecosystems |

**Sources:** nvd.nist.gov · osv.dev

---

## Report Storage Server
**Location:** `mcp_servers/report_storage/server.py`
**Used by:** Report Compiler Agent

Indexes completed review reports for history tracking and retrieval. Does not
write report files — that is handled by `write_report_tool`. Accepts the file
path produced by `write_report_tool` and maintains a queryable index of all
past reviews per repository.

| Tool | Description |
|---|---|
| `save_report` | Index a completed report by repo URL, path, summary, and health score |
| `get_report` | Retrieve a specific report by its report ID |
| `list_reports` | List all past reports for a repository, newest first |
| `diff_reports` | Compare two reports and summarise score changes between them |

---

## Test Runner Server
**Location:** `mcp_servers/test_runner/server.py`
**Used by:** Bug Detection Agent

Runs the repository's existing test suite and returns pass/fail results and
coverage data. Supports auto-detection of the test framework from project files.
Results give the Bug Detection Agent additional context about which areas of
the codebase are tested and which are not.

| Tool | Description |
|---|---|
| `run_tests` | Run the test suite and return pass/fail summary and output |
| `get_coverage_report` | Run tests with coverage and return per-file coverage stats |

**Supported frameworks:** pytest · unittest · jest · mocha · go test