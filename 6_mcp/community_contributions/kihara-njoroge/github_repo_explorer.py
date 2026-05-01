from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import os

load_dotenv()

mcp = FastMCP("github-explorer")

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    "Accept": "application/vnd.github+json",
}


async def gh_get(path: str) -> dict | list | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}{path}", headers=HEADERS, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None


@mcp.tool()
async def get_repo_info(owner: str, repo: str) -> str:
    """Get basic info about a GitHub repository."""
    data = await gh_get(f"/repos/{owner}/{repo}")
    if not data:
        return "Repo not found."
    return (
        f"Name: {data['full_name']}\n"
        f"Description: {data.get('description', 'N/A')}\n"
        f"Stars: {data['stargazers_count']}\n"
        f"Forks: {data['forks_count']}\n"
        f"Language: {data.get('language', 'N/A')}\n"
        f"Open Issues: {data['open_issues_count']}\n"
        f"Default Branch: {data['default_branch']}\n"
        f"URL: {data['html_url']}"
    )


@mcp.tool()
async def list_files(owner: str, repo: str, path: str = "") -> str:
    """List files and directories in a repo path."""
    data = await gh_get(f"/repos/{owner}/{repo}/contents/{path}")
    if not data:
        return "Path not found."
    lines = [f"[{item['type']}] {item['name']}" for item in data]
    return "\n".join(lines)


@mcp.tool()
async def get_file(owner: str, repo: str, path: str) -> str:
    """Get the contents of a file in a repository."""
    data = await gh_get(f"/repos/{owner}/{repo}/contents/{path}")
    if not data or "content" not in data:
        return "File not found or is a directory."
    import base64

    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


@mcp.tool()
async def search_code(owner: str, repo: str, query: str) -> str:
    """Search for code within a specific repository."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/search/code",
                headers=HEADERS,
                params={"q": f"{query} repo:{owner}/{repo}", "per_page": 5},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError:
            return "Search failed."

    if not data.get("items"):
        return "No results found."

    results = []
    for item in data["items"]:
        results.append(f"{item['path']} - {item['html_url']}")
    return "\n".join(results)


@mcp.tool()
async def list_issues(owner: str, repo: str, state: str = "open") -> str:
    """List issues in a repository. State can be open, closed, or all."""
    data = await gh_get(f"/repos/{owner}/{repo}/issues?state={state}&per_page=10")
    if not data:
        return "No issues found."
    results = []
    for issue in data:
        if "pull_request" in issue:
            continue
        results.append(f"#{issue['number']} [{issue['state']}] {issue['title']}")
    return "\n".join(results)


@mcp.tool()
async def get_pr_diff(owner: str, repo: str, pr_number: int) -> str:
    """Get the diff of a pull request."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={**HEADERS, "Accept": "application/vnd.github.diff"},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.text[:8000]
        except httpx.HTTPError:
            return "PR not found."


if __name__ == "__main__":
    mcp.run(transport="stdio")
