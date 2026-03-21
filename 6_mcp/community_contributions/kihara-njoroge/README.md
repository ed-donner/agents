# GitHub Codebase Explorer MCP

An MCP server that lets AI assistants explore GitHub repositories — browse files, read code, search, and inspect issues and pull requests.

## Tools

| Tool | Description |
|---|---|
| `get_repo_info` | Returns repo metadata: stars, forks, language, description |
| `list_files` | Lists files and directories at a given path |
| `get_file` | Returns the full contents of a file |
| `search_code` | Searches for a string or symbol across the repo |
| `list_issues` | Lists open or closed issues |
| `get_pr_diff` | Returns the raw diff of a pull request |

## Setup

```bash
uv add mcp httpx python-dotenv
```

Create a `.env` file:

```
GITHUB_TOKEN=ghp_...
```

Get a token at [github.com/settings/tokens](https://github.com/settings/tokens). Only `repo` read scope is needed.

## Running

```bash
uv add mcp[cli]
mcp dev github_explorer.py
```

This opens a local web UI where you can call and test each tool.

## Claude Desktop Config

```json
{
  "mcpServers": {
    "github-explorer": {
      "command": "uv",
      "args": ["run", "--with", "mcp", "python", "/full/path/to/github_explorer.py"],
      "env": {
        "GITHUB_TOKEN": "ghp_..."
      }
    }
  }
}
```

Config location:
- Linux: `~/.config/Claude/claude_desktop_config.json`
- Mac: `~/Library/Application Support/Claude/claude_desktop_config.json`