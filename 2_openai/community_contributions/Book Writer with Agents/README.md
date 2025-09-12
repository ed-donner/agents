# Project-A

Generative writing pipeline powered by a single Jupyter notebook. It orchestrates outlining, drafting, editing, and exporting a long-form book using OpenAI models, with cost controls, caching, and reproducible outputs.

The primary entry point is `notebook.ipynb`, which:
- Bootstraps the environment (optional pip upgrade, offline-safe)
- Loads `.env` (auto-installs python-dotenv when allowed)
- Defines the book specification (`book_spec`) and pipeline knobs (`pipeline_config`)
- Generates an outline, produces chapter drafts (Author), polishes them (Editor), and assembles the manuscript
- Exports artifacts to DOCX/EPUB and optionally PDF (via docx2pdf or soffice)

Note: Folders such as `content/`, `build/`, `dist/`, `cache/`, and `logs/` are ignored by Git to keep the repo lean.

## Requirements
- Python 3.10+
- Jupyter support (VS Code Python extension or `pip install notebook`)
- OpenAI API key (`OPENAI_API_KEY`)
- For richer export support:
  - `pandoc` in `PATH` (auto-detected; the notebook can attempt installation on Windows via winget/choco/scoop, or fall back to pypandoc when online)
  - For PDF: Microsoft Word + `docx2pdf` on Windows, or LibreOffice/`soffice`

## Quick Start
1) Create a virtual environment
```
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
```

2) Install Jupyter (the notebook handles most runtime deps itself)
```
pip install notebook
```

3) Provide your API key and optional settings
- Create a `.env` file at the repo root, for example:
```
OPENAI_API_KEY=your_key_here
# Optional overrides
# OPENAI_BASE_URL=https://api.openai.com/v1
# OPENAI_ORG=org_123
# OPENAI_PROJECT=proj_123
# OFFLINE=0
```

4) Open and run the notebook
- Open `notebook.ipynb` in VS Code or Jupyter
- Run all cells from top to bottom
- Artifacts are written to `build/` and `dist/`

## Notebook Overview
Stages in the pipeline:
- Environment bootstrap: validates Python/pip, respects `OFFLINE`, optional auto-installs
- Configuration: sets `book_spec` (title, kind, packs, constraints) and `pipeline_config` (models, budgets)
- Agents and routing: authoring, editing, and optional research
- Outline generation: produces a structured outline with guardrails
- Drafting: writes chapter drafts to `content/drafts/`
- Editing: refines drafts and writes to `content/edits/`
- Assembly and QA: creates `build/book.md`, logs cost/manifest to `logs/`
- Export: writes `dist/book.docx`, `dist/book.epub`, and optionally `dist/book.pdf`

## Configuration & Env Vars
Primary environment variables:
- `OPENAI_API_KEY` (required)
- `OPENAI_BASE_URL`, `OPENAI_ORG`/`OPENAI_ORGANIZATION`, `OPENAI_PROJECT` (optional)
- `OPENAI_TIMEOUT` (per-request seconds; default 60)

Book and style:
- `BOOK_KIND` (`fiction`|`nonfiction`; default `fiction`)
- `GENRE_PACK` (fiction) / `STRUCTURE_PACK` (nonfiction)
- `STYLE_PACK` (e.g., academic, journalistic, conversational)
- `CITATION_STYLE` (`none`, `apa`, `chicago`, `ieee`); uses `CSL_STYLE_PATH` for CSL when not `none`

Pipeline and budgets:
- `RUN_COST_CAP_USD` (default `3.0`)
- `CHAPTER_COST_CAP_USD` (default `0.25`)
- `MODEL_ID_FAST` (default `gpt-4o`), `MODEL_ID_THINK` (default `gpt-5`)
- `TEMPERATURE` (default `0.2`)
- `SAMPLE_RUN_CHAPTERS` (default `1`; set `0` to disable)
- `FULL_RUN` (`1`/`0`)
- `ULTRA_BUDGET_MODE` (`1`/`0`) to trim tokens and relax noncritical gates

Export toggles:
- `EXPORT_DOCX`, `EXPORT_EPUB`, `EXPORT_PDF` (each `1`/`0`)

Runtime switches:
- `OFFLINE` (skip network installs and OpenAI client)
- `NO_PIP_UPGRADE` (disable pip auto-upgrade)
- `AUTO_INSTALL_OPENAI`, `AUTO_INSTALL_DOTENV` (permit auto-installs)

You can further adjust chapter templates, token limits, heading formats, and quality gates directly in the Configuration cell of the notebook.

## Repository Structure
- `notebook.ipynb`: End-to-end pipeline (run this)
- `content/`: Working content (outline, research, drafts, edits, style, research_inputs)
- `build/`: Intermediate manuscript (e.g., `build/book.md`)
- `dist/`: Final exports (`book.docx`, `book.epub`, optional `book.pdf`, plus manifests)
- `cache/`: Cached intermediate results to save tokens/cost
- `logs/`: Cost logs, manifests, agent call traces
- `references/`: CSL styles, knowledge bases, story bible (if used)

These directories are listed in `.gitignore` and are safe to delete for a clean rebuild (the notebook will recreate them).

## Troubleshooting
- OPENAI_API_KEY not set: ensure it is available in your environment or `.env`.
- Missing `pandoc`: install via winget/choco/scoop on Windows, or your package manager; the notebook attempts fallbacks when online.
- PDF export skipped/failed: requires Word + `docx2pdf` on Windows or LibreOffice/`soffice`. DOCX/EPUB should still be present.
- Budget exceeded: increase `RUN_COST_CAP_USD` / `CHAPTER_COST_CAP_USD` in env or `pipeline_config`.
- Clean rebuild: stop the kernel, delete `build/`, `dist/`, and `cache/`, then re-run the notebook.

## Notes
- Model usage may incur costs; defaults are conservative. Inspect `logs/` for manifests and cost tracking.
- The default `book_spec` is a customizable scaffold (fiction or nonfiction). Adjust packs and templates to your project.

