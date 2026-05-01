# Frontend Code Reviewer

A week 6 MCP project. An AI agent that reviews React/TypeScript components for accessibility, security, performance, and best practice issues — powered by a custom MCP server with real static analysis tools.

## How it works

`reviewer_server.py` is an MCP server exposing four concrete analysis tools:

| Tool | What it checks |
|---|---|
| `check_accessibility` | Missing alt, non-interactive click handlers, tabIndex, empty buttons, target=_blank without rel |
| `check_security` | dangerouslySetInnerHTML, eval, innerHTML, hardcoded secrets, sensitive localStorage usage |
| `check_performance` | Inline arrow functions in props, array index as key, useEffect without deps, console.log, inline objects |
| `check_best_practices` | TypeScript `any`, `var` usage, loose equality, @ts-ignore, anonymous exports, component size |

The agent calls all four tools, then synthesizes a structured markdown report with: Summary, Critical Issues, Warnings, Quick Wins, and a Verdict.

## Setup

```bash
pip install "agents[openai]" mcp gradio python-dotenv
```

```env
# .env
OPENAI_API_KEY=your_key_here
```

## Usage

### Option A — Gradio UI

```bash
python app.py
```

Paste a component into the editor, enter a file path, or enter a directory path, then click **Review**.

---

### Option B — Use directly with Claude Code

This connects the MCP server to Claude so you can review files from your own repo without leaving the terminal.

**1. Start the MCP server in SSE mode**

```bash
uv run reviewer_server.py --transport sse --port 8000
```

Keep this running in a terminal.

**2. Register it with Claude Code**

```bash
claude mcp add --transport sse frontend-reviewer http://localhost:8000/sse
```

Or add it manually to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "frontend-reviewer": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**3. Navigate to your project and start Claude**

```bash
cd ~/your-frontend-project
claude
```

Then ask naturally:

> "Review `src/components/PaymentForm.tsx` for accessibility and security issues"

> "Check everything in `src/components/` for performance anti-patterns"

> "Does `src/pages/checkout.tsx` have any XSS risks?"

Claude will call the MCP tools directly and return a structured report. The `read_file` and `list_source_files` tools mean Claude can read your files itself — no copy-pasting needed.

## Example output

```
# Code Review Report

## Summary
The component has one critical XSS risk and two accessibility issues...

## Critical Issues
- **dangerouslySetInnerHTML without sanitization** — XSS risk if `content` comes
  from user input. Fix: wrap with DOMPurify.sanitize(content) before passing in.

## Warnings
- 3 inline arrow functions in onClick props — wrap in useCallback if passed to
  memoized children to avoid unnecessary re-renders.

## Verdict
NEEDS WORK — address the XSS issue before shipping.
```
