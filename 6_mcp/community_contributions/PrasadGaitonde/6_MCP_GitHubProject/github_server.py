import os
from typing import List, Optional
from fastmcp import FastMCP
from github import Github, GithubException

# Initialize FastMCP server
mcp = FastMCP("GitHub Agent")

# Initialize GitHub client
# We assume GITHUB_TOKEN is set in the environment
def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set")
    return Github(token)

@mcp.tool()
def get_repo_structure(owner: str, repo: str, path: str = "") -> str:
    """
    Provides a tree view of the repository at the specified path.
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        contents = repository.get_contents(path)

        structure = []
        for item in contents:
            prefix = "📁" if item.type == "dir" else "📄"
            structure.append(f"{prefix} {item.path}")

        return "\n".join(structure) if structure else "Directory is empty."
    except GithubException as e:
        return f"Error fetching repo structure: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool()
def read_file(owner: str, repo: str, path: str) -> str:
    """
    Reads the content of a specific file from a GitHub repository.
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        content = repository.get_contents(path).decoded_content
        return content.decode("utf-8")
    except GithubException as e:
        return f"Error reading file: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool()
def create_issue(owner: str, repo: str, title: str, body: str) -> str:
    """
    Creates a new issue in the specified GitHub repository.
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        issue = repository.create_issue(title=title, body=body)
        return f"Issue created successfully: {issue.html_url}"
    except GithubException as e:
        return f"Error creating issue: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool()
def list_prs(owner: str, repo: str, state: str = "open") -> str:
    """
    Lists pull requests in a GitHub repository based on the state (open, closed, all).
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        pulls = repository.get_pulls(state=state, sort="created", direction="descending")

        pr_list = []
        for pr in pulls:
            pr_list.append(f"#{pr.number}: {pr.title} (Author: {pr.user.login}) - {pr.html_url}")

        return "\n".join(pr_list) if pr_list else "No pull requests found."
    except GithubException as e:
        return f"Error listing PRs: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool()
def create_pull_request(owner: str, repo: str, title: str, head: str, base: str, body: str) -> str:
    """
    Creates a new pull request in the specified GitHub repository.
    - head: The name of the branch where your changes are implemented.
    - base: The name of the branch you want the changes merged into.
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        pr = repository.create_pull(title=title, body=body, head=head, base=base)
        return f"Pull request created successfully: {pr.html_url}"
    except GithubException as e:
        return f"Error creating pull request: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@mcp.tool()
def search_code(query: str) -> str:
    """
    Searches for code across GitHub repositories based on the query.
    """
    try:
        g = get_github_client()
        results = g.search_code(query=query)

        search_results = []
        for item in results:
            search_results.append(f"File: {item.path} in {item.repository.full_name} - {item.html_url}")

        return "\n".join(search_results) if search_results else "No code matches found."
    except GithubException as e:
        return f"Error searching code: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Resources
@mcp.resource("github://repo/{owner}/{repo}/files")
def get_repo_files(owner: str, repo: str) -> str:
    """
    Returns the root directory listing of a repository.
    """
    return get_repo_structure(owner, repo)

@mcp.resource("github://issue/{owner}/{repo}/{issue_number}")
def get_issue_details(owner: str, repo: str, issue_number: int) -> str:
    """
    Returns details of a specific GitHub issue.
    """
    try:
        g = get_github_client()
        repository = g.get_repo(f"{owner}/{repo}")
        issue = repository.get_issue(number=issue_number)
        return f"Title: {issue.title}\nState: {issue.state}\nBody: {issue.body}"
    except GithubException as e:
        return f"Error fetching issue details: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

if __name__ == "__main__":
    mcp.run()
