# 🤖 AI Code Review & Refactor Agent System

An automated multi-agent code review pipeline built with the **OpenAI Agents SDK** and **Python**. The system accepts a GitHub repository URL or a local directory path, runs it through a pipeline of specialist agents, and produces a structured Markdown report covering bugs, refactoring opportunities, and security vulnerabilities.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agentic Pattern](#agentic-pattern)
- [Agents](#agents)
- [Tools](#tools)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Output](#output)
- [Guardrails](#guardrails)
- [Supported Languages](#supported-languages)
- [Adding a New Language](#adding-a-new-language)

---

## Overview

This project demonstrates the **Orchestrator + Agents-as-Tools** agentic pattern. A central Orchestrator Agent coordinates the entire pipeline by calling specialist agents as tools — retaining full control of the workflow at all times. Each specialist agent is responsible for one concern: structural analysis, bug detection, refactoring, security auditing, or report compilation.

The system is designed to be:

- **Modular** — each agent is independently defined and can be extended or replaced
- **Robust** — guardrails validate inputs and outputs at critical points in the pipeline
- **Language-agnostic** — supports 13 programming languages via `tree-sitter`
- **Production-ready** — structured outputs, error handling, and cleanup at every step

---

## Architecture

```
User Input (GitHub URL or local path)
        │
        ▼
┌─────────────────────┐
│  Orchestrator Agent │  ← Controls the entire pipeline
└─────────────────────┘
        │
        ├──► Code Analysis Agent    → code_map + chunks
        │
        ├──► Bug Detection Agent    → bugs
        │
        ├──► Refactor Agent         → refactor_suggestions
        │
        ├──► Security Audit Agent   → security_findings
        │
        └──► Report Compiler Agent  → Final Markdown Report
```

Data flows entirely in memory through the Orchestrator. No inter-agent file I/O is needed — findings are passed as return values from each agent tool call.

---

## Agentic Pattern

**Pattern:** Orchestrator + Agents-as-Tools (Hierarchical)

The Orchestrator Agent calls each specialist agent using the OpenAI Agents SDK `as_tool()` method. This means:

- The Orchestrator **never transfers control** — it calls agents like functions and gets results back
- Each specialist agent runs in its own context with its own tools and instructions
- The Orchestrator assembles all results and passes them to the Report Compiler

---

## Agents

### 🧠 Orchestrator Agent
Coordinates the entire pipeline. Receives user input, clones or reads the repository, calls each specialist agent in sequence, collects all findings, and delivers the final report. Never performs code analysis itself.

**Tools:** `clone_repo_tool`, `read_files_tool`, `cleanup_repo_tool`
**Agent Tools:** All five specialist agents via `as_tool()`

---

### 🔍 Code Analysis Agent
Reads and parses the codebase into a structured code map and chunked output. Every downstream agent depends on its output.

**Tools:** `parse_code_tool`, `chunk_code_tool`

---

### 🐛 Bug Detection Agent
Analyzes code chunks for bugs, logical errors, unhandled exceptions, resource leaks, and incorrect API usage. Returns findings ranked by severity.

**Tools:** None — the agent's own LLM reasoning performs the analysis over the chunks it receives
**Guardrail:** Output guardrail validates descriptions, severity distribution, and line numbers

---

### ✨ Refactor Suggestion Agent
Reviews code for quality issues including duplication, poor naming, missing type hints, deep nesting, dead code, and violations of the Single Responsibility Principle.

**Tools:** None — analysis performed by the agent's own LLM reasoning

---

### 🔒 Security Audit Agent
Scans code for security vulnerabilities including hardcoded secrets, injection risks, insecure deserialization, path traversal, weak cryptography, and exposed debug modes.

**Tools:** `WebSearchTool` (for CVE and security advisory lookups)
**Guardrail:** Output guardrail checks CRITICAL recommendations, zero-findings advisory, and secret leakage detection

---

### 📝 Report Compiler Agent
Compiles all findings from the three review agents into a single structured Markdown report with an executive summary, severity-ranked findings, a files table, and a prioritised action plan.

**Tools:** `write_report_tool`

---

## Tools

| Tool | File | Used By | Purpose |
|---|---|---|---|
| `clone_repo_tool` | `tools/file_tools.py` | Orchestrator | Clones a GitHub repo into a temp directory |
| `read_files_tool` | `tools/file_tools.py` | Orchestrator | Reads source files from a local directory |
| `cleanup_repo_tool` | `tools/file_tools.py` | Orchestrator | Deletes the temp directory after pipeline completes |
| `parse_code_tool` | `tools/parser_tools.py` | Code Analysis Agent | Parses source files into a structured code map |
| `chunk_code_tool` | `tools/parser_tools.py` | Code Analysis Agent | Splits large files into LLM-safe chunks |
| `WebSearchTool` | OpenAI Agents SDK | Security Audit Agent | Searches for CVEs and security advisories |
| `write_report_tool` | `tools/report_tools.py` | Report Compiler Agent | Writes the final Markdown report to disk |

---

## Project Structure

```
code-review-agents/
├── agency/                        # Agent definitions
│   ├── __init__.py
│   ├── orchestrator.py            # Orchestrator Agent
│   ├── code_analysis.py           # Code Analysis Agent
│   ├── bug_detection.py           # Bug Detection Agent
│   ├── refactor.py                # Refactor Suggestion Agent
│   ├── security.py                # Security Audit Agent
│   └── report_compiler.py         # Report Compiler Agent
├── tools/                         # Tool definitions
│   ├── __init__.py
│   ├── file_tools.py              # clone_repo_tool, read_files_tool, cleanup_repo_tool
│   ├── parser_tools.py            # parse_code_tool, chunk_code_tool
│   └── report_tools.py            # write_report_tool
├── guardrails/                    # Guardrail definitions
│   ├── __init__.py
│   ├── input_guardrail.py         # Orchestrator input guardrail
│   ├── bug_guardrail.py           # Bug Detection output guardrail
│   └── security_guardrail.py      # Security Audit output guardrail
├── schemas/                       # Pydantic structured output schemas
│   ├── __init__.py
│   ├── code_analysis_schema.py
│   ├── bug_schema.py
│   ├── refactor_schema.py
│   └── security_schema.py
├── main.py                        # Entry point
├── .env                           # Environment variables (not committed)
├── .env.example                   # Example environment file
├── .gitignore
└── requirements.txt
```

---

## Prerequisites

- Python 3.11 or higher
- An [OpenRouter](https://openrouter.ai) account with API credits
- Git installed on your system

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/ed-donner/agents.git
cd agents/2_openai/community_contributions/code_rewiewer
```

**2. Create and activate a virtual environment**

```bash
uv venv
```

**3. Install dependencies**

```bash
uv sync
```

**`requirements.txt`**
```
openai-agents
gitpython
tree-sitter
tree-sitter-languages
python-dotenv
gradio
```

---

## Configuration

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

**`.env.example`**
```env
# OpenRouter settings
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=your_openrouter_api_key_here
GPT_MODEL=gpt-4o-mini
CLAUDE_MODEL=claude-sonnet-4.6

# Output directory for generated reports
REPORT_OUTPUT_DIR=./reports
```

---

## Usage

**Run with the Gradio UI**

```bash
uv run main.py
```

Then open `http://localhost:7860` in your browser and enter one of the following:

- A GitHub URL: `https://github.com/username/repo`
- A local path: `C:\projects\myrepo` or `/home/user/projects/myrepo`
- Natural language: `Please review https://github.com/username/repo for me`

---

## Output

The pipeline produces a Markdown report saved to the `REPORT_OUTPUT_DIR` directory with the following sections:

| Section | Contents |
|---|---|
| Executive Summary | File count, line count, finding counts, health score out of 10, overall assessment |
| Bug Findings | Grouped by severity (CRITICAL → HIGH → MEDIUM → LOW) with file, line, description, and fix suggestion |
| Refactor Suggestions | Grouped by priority with category, description, and actionable improvement |
| Security Vulnerabilities | Grouped by severity with description of exploit risk and concrete remediation |
| Files Reviewed | Table of all files with line counts and parse status |
| Recommended Action Plan | Prioritised numbered list of the most critical actions across all categories |

**Example report filename:**
```
reports/code_review_report_20250101_143022.md
```

---

## Guardrails

The system uses three guardrails to enforce quality and safety at critical points:

### Input Guardrail — Orchestrator Agent
Validates user input before the pipeline starts. Uses an LLM to intelligently extract URLs or paths from natural language. Blocks invalid GitHub URLs and local paths that do not exist on disk. Allows plain conversational input through so the Orchestrator can respond helpfully.

### Output Guardrail — Bug Detection Agent
Checks that descriptions are specific and actionable, that severity levels are not inflated (flags if more than 40% of findings are CRITICAL), and that every finding has a valid line number.

### Output Guardrail — Security Audit Agent
Checks that CRITICAL findings have substantive recommendations, flags zero findings on non-trivial codebases as an advisory, and scans finding text for patterns matching real secret formats to prevent accidental secret leakage into the report.

---

## Supported Languages

| Language | Extension |
|---|---|
| Python | `.py` |
| JavaScript | `.js` |
| TypeScript | `.ts` |
| Java | `.java` |
| Go | `.go` |
| Ruby | `.rb` |
| PHP | `.php` |
| C# | `.cs` |
| C++ | `.cpp` |
| C | `.c`, `.h` |
| Rust | `.rs` |
| Swift | `.swift` |
| Kotlin | `.kt` |

Python files use the built-in `ast` module for richer extraction (type hints, docstrings). All other languages use `tree-sitter` via the `tree-sitter-languages` package.

---

## Adding a New Language

Three changes are required in `tools/parser_tools.py`:

**Step 1 — Add to `LANGUAGE_MAP`:**
```python
".ex": ("elixir", "elixir"),
```

**Step 2 — Add to `LANGUAGE_QUERIES`:**
```python
"elixir": {
    "class":    ["defmodule"],
    "function": ["def", "defp"],
    "import":   ["alias", "import", "use"],
},
```

**Step 3 — Add to `SUPPORTED_EXTENSIONS` in `tools/file_tools.py`:**
```python
SUPPORTED_EXTENSIONS = {
    ...,
    ".ex"
}
```

No other changes are needed anywhere in the codebase.