# Job Scout Pipeline

A small agentic-AI job search pipeline that:
- searches LinkedIn and Indeed job listings via JobSpy,
- prefilters likely matches,
- evaluates shortlisted roles against a candidate profile,
- lets you review ranked jobs in a Gradio UI,
- generates tailored cover letters as PDFs for selected roles.

## Pipeline

1. **Scout** (`job_search.py`) -> `jobs_raw.json`
2. **Prefilter** (`job_prefilter.py`) -> `jobs_shortlisted.json`
3. **Evaluator** (`job_evaluator.py`) -> `jobs_ranked.json`
4. **UI** (`job_ui.py`) -> select jobs + generate cover letters

## Current architecture

- **Scout** uses JobSpy MCP to fetch search results from LinkedIn and Indeed.
- `full_description` is captured during the Scout step and carried through the pipeline.
- **Evaluator** and **Cover Letter** stages no longer scrape job pages with Firecrawl.
- This makes the pipeline simpler and avoids LinkedIn scraping limitations.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) recommended
- OpenAI API key
- Node.js is only needed if your local JobSpy MCP setup requires it

## Setup

1. Clone the repository.
2. Create a virtual environment / use `uv`.

```bash
uv sync
```

3. Copy the example files:

```bash
cp .env.example .env
cp config.example.yaml config.yaml
cp profile.example.md profile.md
cp criteria.example.md criteria.md
```

4. Fill in your own values in:
- `.env`
- `config.yaml`
- `profile.md`
- `criteria.md`

## Environment variables

Only one environment variable is required:

```bash
OPENAI_API_KEY=your_key_here
```

## Run

Full pipeline:

```bash
uv run python app.py
```

Skip Scout and reuse existing raw jobs:

```bash
uv run python app.py --skip-search
```

Launch UI only:

```bash
uv run python app.py --ui-only
```

Run individual stages:

```bash
uv run python job_search.py
uv run python job_prefilter.py
uv run python job_evaluator.py
uv run python job_ui.py
uv run python cover_letter.py
```

## Output files

Generated checkpoint files:
- `jobs_raw.json`
- `jobs_shortlisted.json`
- `jobs_ranked.json`
- `jobs_selected.json`
- `cover_letters/`

These are treated as generated artifacts and are ignored in git.

## Personalization model

The repository is designed so user-specific information lives outside source code:
- `config.yaml` for candidate/search settings,
- `profile.md` for detailed background,
- `criteria.md` for job targeting preferences,
- `.env` for secrets.

Only example/template versions of those files should be committed.

## Notes

- LinkedIn scraping via Firecrawl is intentionally not used.
- The Evaluator writes **all scored jobs** to `jobs_ranked.json`, not only the top 10.
- `top_n` is now only used for display/emphasis, not persistence.
