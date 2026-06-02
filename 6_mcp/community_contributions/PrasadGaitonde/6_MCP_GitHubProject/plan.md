 Implementation Plan: GitHub MCP Agent

 Context

 The goal is to implement a GitHub Agent that follows the modular MCP (Model Context Protocol) architecture established in the current project. This architecture separates
 domain-specific logic into standalone MCP servers and uses a client bridge to expose those capabilities to an LLM. The GitHub Agent will allow the LLM to interact with GitHub
  repositories, issues, and pull requests while maintaining the same observability and configuration patterns.

 Recommended Approach

 1. GitHub MCP Server

 Create a new server using the FastMCP framework to encapsulate GitHub API interactions.
 - File: /home/prasad/projects/agents/6_mcp/community_contributions/PrasadGaitonde/6_MCP_GitHubProject/github_server.py
 - Dependencies: FastMCP, PyGithub (or httpx)
 - Authentication: Load GITHUB_TOKEN from environment variables.
 - Implementation:
   - Tools:
       - get_repo_structure(owner, repo, path=""): Tree view of the repository.
     - read_file(owner, repo, path): Read content of a specific file.
     - create_issue(owner, repo, title, body): Open a GitHub issue.
     - list_prs(owner, repo, state="open"): List pull requests.
     - create_pull_request(owner, repo, title, head, base, body): Create a new PR.
     - search_code(query): Search across repositories.
   - Resources:
       - github://repo/{owner}/{repo}/files: Directory listings.
     - github://issue/{owner}/{repo}/{issue_number}: Issue context.

 2. GitHub Client Bridge

 Create a client to manage the session and translate tools for the LLM.
 - File: /home/prasad/projects/agents/6_mcp/community_contributions/PrasadGaitonde/6_MCP_GitHubProject/github_client.py
 - Implementation:
   - Initialize a stdio_client session with the github_server.py.
   - Implement get_github_tools_openai() to convert MCP tool definitions to LLM-compatible function schemas.
   - Implement read_github_resource(uri) to retrieve resource data.
   - Create a wrapper for tool execution that integrates with the system's tracing.

 3. Configuration and Integration

 Integrate the new server into the existing orchestration layer.
 - File: /home/prasad/projects/agents/6_mcp/community_contributions/PrasadGaitonde/6_MCP_GitHubProject/mcp_params.py
 - Action: Add a configuration entry for the GitHub server:
 github_mcp = {
     "command": "uv",
     "args": ["run", "github_server.py"],
     "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
 }
 4. Observability

 Ensure all agent actions are recorded.
 - Reference: Use tracers.py and database.py.
 - Action: Wrap github_client tool calls in LogTracer spans so that every GitHub API interaction is persisted in the SQLite database for auditing.

 Verification Plan

 1. Server Validation: Run github_server.py independently and test tools using the MCP Inspector or a basic shell script.
 2. Client Integration: Instantiate github_client.py and verify that get_github_tools_openai() returns the correct JSON schemas.
 3. End-to-End Flow:
   - Prompt the agent to "List open PRs in [repo]" and "Create an issue describing [bug]".
   - Verify the actions appear in the GitHub UI.
   - Check the local SQLite database via database.py to ensure the traces were recorded correctly.
