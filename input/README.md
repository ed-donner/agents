# Feedback input

Drop feedback files into this folder, then run the analyzer:

```bash
uv run python workflows/feedback_analyzer.py
```

Supported formats:

- **CSV:** one row per response. The text column must be named `text`, `feedback`, `comment`, `body`, or `response`. An optional `date` column is used when present.
- **TXT / MD:** blank lines separate individual feedback items.
- **JSON:** a list of strings, or a list of objects with a `text` field.
- **PDF:** text is extracted, and blank lines separate items.

Files that cannot be parsed are listed in the report under "Skipped files". They are not silently dropped.

Results are written to `output/report.md` and `output/themes.csv`.
