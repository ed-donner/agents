# Feedback Analyzer Workflow

Analyzes feedback files dropped into an input folder, groups them into themes, and scores each theme by frequency and severity.

## Context

- **Product:** software app or web product
- **Audience:** product team (PM and engineering)
- **Decisions supported:**
  - What to fix next
  - What to build next
  - Health tracking over time
  - Where to invest in support or docs
- **Input format:** not yet decided. The first version supports CSV, TXT, MD, JSON, and PDF.

## Steps

1. **Trigger.** A new file lands in `input/`. The workflow runs on demand, or checks for new files when started. No watcher process in v1. A manifest records processed files so nothing is analyzed twice.

2. **Read and normalize.** Each file is parsed into a common record: `id`, `text`, `date`, `source_file`, plus optional metadata such as rating or user segment. Files that cannot be parsed are logged and skipped, never dropped silently.

3. **Group into themes.** The model proposes themes from each batch, then merges them into a stable list so a theme keeps the same name across runs. Each theme has a short definition and a few representative quotes. Each feedback item may carry more than one theme.

4. **Score each theme.**
   - **Frequency:** share of feedback items that mention the theme.
   - **Severity:** 1–5 per item, using a rubric:
     - 5: blocks a core task or causes data loss
     - 3: friction with a workaround
     - 1: cosmetic or a wish
   - **Theme severity:** average of its item scores, with the worst cases called out separately.
   - **Priority:** frequency × severity. Both numbers are shown so the ranking can be explained.

5. **Report.** A single report containing:
   - Top themes for "what to fix next" and "what to build next". Bugs and feature requests are labeled separately.
   - Health trend across batches, showing whether each theme is growing or shrinking. Only when there is more than one batch.
   - Support and docs view: themes that look like confusion or missing documentation.
   - Appendix: theme definitions, scoring details, and example quotes.

6. **Output.** Written to `output/` as Markdown, plus a CSV of scored themes for pasting into a tracker.

## Decisions

- **Scoring method:** keyword-based. No model calls for theme or severity scoring, so the workflow is free to run. Themes are defined as keyword lists, and severity uses keyword rules that map to the 1–5 rubric.

## Built files

- `input/README.md`: how to drop files and which formats are supported
- `workflows/feedback_analyzer.py`: the analyzer (standard library plus `pypdf` for PDFs)
- `workflows/themes.json`: keyword lists for each theme, with a type of bug, usability, or request. These are starter guesses, to be tuned on real feedback.
- `workflows/severity.json`: keyword rules that set severity levels 1, 3, and 5

Run with `uv run python workflows/feedback_analyzer.py`. Output goes to `output/report.md` and `output/themes.csv`.

## Deviations from the plan

- No manifest. Each run analyzes every file in `input/`, so nothing is skipped or double-counted within a run. Health trends across batches are not implemented yet.
- Theme review before scoring is not built in. Adjust `themes.json` by hand instead.

## Open decisions

- Input file format and volume per batch: still unknown. The current parsers cover the formats listed in `input/README.md`.
