from mcp.server.fastmcp import FastMCP
from issues import IssueStore

mcp = FastMCP("issues_server")
store = IssueStore()


@mcp.tool()
async def add_issue(issue: str, command: str, project_path: str) -> str:
    """Record a developer issue with the command used to solve it.

    Args:
        issue: description of the issue encountered
        command: the command or series of commands that solved the issue, include commands only without extra text.
        project_path: the project directory where the issue occurred
    """
    issue_id = store.add_issue(issue, command, project_path)
    return f"Issue #{issue_id} added successfully."


@mcp.tool()
async def search_issues(keywords: list[str]) -> list[dict]:
    """Search for previously solved issues by keywords.

    Args:
        keywords: list of words to match against stored issues
    """
    results = store.search_issues(keywords)
    if not results:
        return [{"message": "No matching issues found."}]
    return results


@mcp.tool()
async def read_log_file() -> str:
    """Read the contents of the terminal activity log to help find if the are issues and log the resolving commands."""
    return store.read_log_file()

@mcp.tool()
async def clear_log() -> str:
    """Clear the log file ."""
    return store.clear_log()

if __name__ == "__main__":
    mcp.run(transport="stdio")