# Sidekick Proj - AI Co-Worker

LangGraph-based AI assistant with web browsing, search, and file management capabilities.

## Features

- **Web Search**: Google search for finding information
- **Web Browsing**: Navigate and extract content from websites
- **File Creation**: Save files in any format (Markdown, HTML, Python, JSON, etc.)
- **Code Execution**: Run Python code
- **Wikipedia**: Encyclopedia information

## Usage

```bash
uv run python -m 4_langgraph.community_contributions.sidekick_proj.app
```

## How It Works

1. **Search first**: Uses Google search to find relevant websites
2. **Browse**: Visits URLs from search results to extract detailed information
3. **Save**: Creates files in the `sandbox/` directory when requested

## Example

"Recommend top 10 hotels in HomaBay Town, Kenya and save results in hotels_in_homabay.md"

The sidekick will search, browse relevant sites, compile information, and save to a Markdown file.
