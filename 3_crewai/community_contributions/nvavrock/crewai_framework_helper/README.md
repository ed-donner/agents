# CrewAI Framework Helper

A **community contribution** for CrewAI week: a small crew that answers questions about the CrewAI framework using **RAG over indexed upstream source and docs** — not guesses.

Two agents run in sequence:

1. **Framework researcher** — searches the index with `framework_search`
2. **Framework advisor** — writes a cited answer to `output/answer.md`

Related work: [Smart Coder](https://github.com/nvavrock/crewAI) uses the same RAG pattern to scaffold full projects. This contribution is a trimmed, course-friendly Q&A crew.

## Requirements

- Python `>=3.10,<3.14`
- [uv](https://docs.astral.sh/uv/) package manager
- **OpenAI API key** — required for bootstrap embeddings and agent LLMs (`gpt-4o-mini`)
- **CrewAI CLI** (optional) — `uv tool install crewai==1.14.4` per course week 3; or use `uv run crewai run` below

**Windows:** Chroma may require [MS Build Tools](https://github.com/bycloudai/InstallVSBuildToolsWindows) if install fails.

## Setup

```bash
cd 3_crewai/community_contributions/nvavrock/crewai_framework_helper
cp .env.example .env   # add OPENAI_API_KEY
uv sync
```

## Bootstrap the index (required before first run)

Clones `crewAIInc/crewAI` into `upstream/crewai/` and embeds lib + docs into `.rag_index/`:

```bash
uv run bootstrap-index --yes
```

Or: `uv run python scripts/bootstrap_index.py --yes`

## Run the crew

```bash
uv run crewai run
```

Or with a custom question:

```bash
QUESTION="How do I use Flow with @start and @listen?" uv run crewai run
```

Output: `output/answer.md` with explanation, code example, and **Sources** section.

**Sources paths** are relative to `upstream/crewai/` (the local clone created during bootstrap). After each run, a note is appended to `answer.md` explaining that those files may not exist on your machine until you bootstrap, or if your upstream ref differs. The same paths exist on [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) on GitHub.

## Example questions

- How do I use CrewBase with YAML agent configs?
- How do I add a custom tool with BaseTool?
- How do I configure crew-level knowledge from text files?
- What is the difference between @start and @listen on a Flow?

## Verify the index (optional)

```bash
uv run eval-rag
```

Runs golden queries from `eval/rag_queries.yaml` (embedding search only during eval).

## Local-only paths (gitignored)

- `.rag_index/` — Chroma embeddings
- `upstream/crewai/` — cloned framework repo
- `output/` — generated answers
