# CrewAI Framework Helper

A small crew that answers CrewAI framework questions using **RAG over indexed upstream source and docs** — not guesses.

**Pattern:** clone `crewAIInc/crewAI` → embed lib + docs into Chroma → expose a `framework_search` tool → two agents research then write a cited answer to `output/answer.md`.

## Setup

```bash
cd 3_crewai/community_contributions/nvavrock/crewai_framework_helper
cp .env.example .env   # add OPENAI_API_KEY
uv sync
uv run bootstrap-index --yes   # clones upstream/crewai, builds .rag_index/
uv run crewai run
```

Custom question: `QUESTION="How do Flow @start and @listen work?" uv run crewai run`

## What's unique here

| Piece | File |
|-------|------|
| RAG (clone, index, search) | `src/crewai_framework_helper/rag.py` |
| Custom tool | `src/crewai_framework_helper/tools/framework_search.py` |
| Crew | `src/crewai_framework_helper/crew.py` + YAML configs |

Everything else follows the standard `crewai create crew` layout. To replicate for another repo, copy `rag.py` and `framework_search.py`, point `UPSTREAM_REPO_URL` at your target, and adjust `INDEX_PATHS`.

## Verify retrieval (optional)

```bash
uv run python -c "from crewai_framework_helper.rag import format_results, search; print(format_results(search('CrewBase decorator')))"
```

## Gitignored (local only)

`.rag_index/`, `upstream/crewai/`, `output/`
