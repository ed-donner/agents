# AI Code Review & Refactor Agent

Multi-agent code review pipeline using the **OpenAI Agents SDK** and Python. An **Orchestrator** calls specialist agents via `as_tool()` (no handoff of control); specialists analyze chunks and the **Report Compiler** writes one Markdown report.

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Orchestrator** | Clone/read repo, run pipeline, cleanup | `clone_repo_tool`,  `cleanup_repo_tool` + all specialists as tools |
| **Code Analysis** | Parse repo → code map + chunks | `parse_code_tool`, `chunk_code_tool`, `read_files_tool` |
| **Bug Detection** | Bugs, logic errors, leaks, bad API use | Nil |
| **Refactor** | Quality, duplication, naming, structure | Nil |
| **Security** | Secrets, injection, crypto, etc. | `WebSearchTool` |
| **Report Compiler** | Single Markdown report | `write_report_tool` |

## Tool locations

| Tool | File |
|------|------|
| `clone_repo_tool`, `read_files_tool`, `cleanup_repo_tool` | `tools/file_tools.py` |
| `parse_code_tool`, `chunk_code_tool` | `tools/parser_tools.py` |
| `write_report_tool` | `tools/report_tools.py` |
| `WebSearchTool` | OpenAI Agents SDK |

## MCP Servers
Refer to the README.md file in /6_mcp/community_contributions/code_reviewer_mcp_servers' directory for the description of the MCP servers.

## Setup

- **Requires:** Python ≥3.11, Git, [OpenRouter](https://openrouter.ai) API credits

```bash
git clone https://github.com/ed-donner/agents.git
cd agents/2_openai/community_contributions/code_reviewer
uv venv
uv sync
```

Create `.env`:

- `OPENROUTER_BASE_URL`
- `OPENROUTER_API_KEY`
- `GPT_MODEL`, `CLAUDE_MODEL`
- `REPORT_OUTPUT_DIR=./reports`
- `TEST_RUNNER_TIMEOUT`

Dependencies: see `requirements.txt` (`openai-agents`, `gradio`, `gitpython`, `tree-sitter`, `tree-sitter-languages`, `python-dotenv`, `pydantic`).

## Run

```bash
uv run main.py
```

Open `http://localhost:7860`. Input: GitHub URL, local path, or natural language containing a URL/path.

Reports: `REPORT_OUTPUT_DIR`, e.g. `reports/code_review_report_YYYYMMDD_HHMMSS.md` — executive summary, bugs/refactors/security by severity, files table, action plan.

## Guardrails

- **Orchestrator (input):** Extract URL/path from text; block bad URLs and missing paths.
- **Bug output:** Actionable text, sane CRITICAL share, valid line numbers.
- **Security output:** Substantive CRITICAL advice, advisory on empty findings for large codebases, secret-pattern scan on text.

## Parsed languages

`.py`, `.js`, `.ts`, `.java`, `.go`, `.rb`, `.php`, `.cs`, `.cpp`, `.c`, `.h`, `.rs`, `.swift`, `.kt`