# README truth checker (AutoGen AgentChat)

Multi-agent flow that **extracts checkable claims** from a project’s README, **verifies them** with safe, repo-scoped filesystem tools, and **writes a short markdown report** with suggested fixes.

## What it demonstrates

- **Week 5 AgentChat**: `AssistantAgent`, `RoundRobinGroupChat`, `TextMentionTermination`, `CancellationToken`
- **Structured output**: `ClaimBundle` / `DocClaim` via `output_content_type` on a solo `on_messages` call (Lab 2). The verifier/reporter run in a **round-robin team** using plain text only, because group chat does not register `StructuredMessage` for custom schemas.
- **Tool-grounded checks**: no shell execution; paths are confined to the chosen project root

## Requirements

- Dependencies from the repo root `pyproject.toml` (e.g. `autogen-agentchat`, `autogen-ext`, `python-dotenv`)
- `OPENAI_API_KEY` in the environment (or `.env`)

## Run

From this directory:

```bash
cd 5_autogen/community_contributions/readme_truth_checker
python main.py
```

Default `--root` points at `fixtures/sample_project`, whose README is **intentionally wrong** (wrong filenames and paths) so you can see FAIL results.

Check another project:

```bash
python main.py --root /path/to/your/repo
```

## Agents

1. **claims_extractor** (phase 1) — structured claims from the README via `on_messages`  
2. **filesystem_verifier** (phase 2, team) — `list_directory`, `read_text_file`, `path_exists`, `glob_relative`  
3. **report_editor** (phase 2, team) — consolidated markdown; ends with `### README_CHECK_DONE ###` (avoids matching the initial user task)

## Safety

Tools resolve paths under the given root only; absolute paths and `..` segments are rejected.
