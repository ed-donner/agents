"""Keyword-based feedback analyzer.

Reads feedback files from input/, groups items into themes defined in
workflows/themes.json, scores each theme, and writes output/report.md
and output/themes.csv.

Run from the repo root:
    uv run python workflows/feedback_analyzer.py
"""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
THEMES_PATH = ROOT / "workflows" / "themes.json"
SEVERITY_PATH = ROOT / "workflows" / "severity.json"

SUPPORTED = {".csv", ".txt", ".md", ".json", ".pdf"}
TEXT_COLUMNS = ("text", "feedback", "comment", "body", "response")
EXAMPLES_PER_THEME = 3
MAX_QUOTE_CHARS = 200


def split_items(content):
    """Split free text into items separated by blank lines."""
    return [chunk.strip() for chunk in re.split(r"\n\s*\n", content) if chunk.strip()]


def parse_csv(path):
    records = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = {name.lower(): name for name in reader.fieldnames or []}
        text_column = next((columns[c] for c in TEXT_COLUMNS if c in columns), None)
        if text_column is None:
            raise ValueError(f"no text column found (expected one of {', '.join(TEXT_COLUMNS)})")
        date_column = columns.get("date")
        for row in reader:
            text = (row.get(text_column) or "").strip()
            if text:
                date = (row.get(date_column) or "").strip() if date_column else ""
                records.append({"text": text, "date": date})
    return records


def parse_json(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expected a JSON list")
    records = []
    for entry in data:
        text = entry.get("text") if isinstance(entry, dict) else entry
        if isinstance(text, str) and text.strip():
            date = entry.get("date", "") if isinstance(entry, dict) else ""
            records.append({"text": text.strip(), "date": str(date)})
    return records


def parse_pdf(path):
    from pypdf import PdfReader

    content = "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return [{"text": item, "date": ""} for item in split_items(content)]


def parse_text(path):
    content = path.read_text(encoding="utf-8")
    return [{"text": item, "date": ""} for item in split_items(content)]


PARSERS = {
    ".csv": parse_csv,
    ".json": parse_json,
    ".pdf": parse_pdf,
    ".txt": parse_text,
    ".md": parse_text,
}


def keyword_hit(keyword, text):
    return re.search(r"\b" + re.escape(keyword.lower()) + r"\b", text) is not None


def analyze(record, themes, severity_rules):
    text = record["text"].lower()
    matched = [
        name
        for name, cfg in themes.items()
        if any(keyword_hit(kw, text) for kw in cfg["keywords"])
    ]
    levels = [
        level
        for level, keywords in severity_rules.items()
        if any(keyword_hit(kw, text) for kw in keywords)
    ]
    return {**record, "themes": matched, "severity": max(levels, default=1)}


def theme_stats(analyzed, themes):
    total = len(analyzed)
    stats = []
    for name, cfg in themes.items():
        items = [r for r in analyzed if name in r["themes"]]
        if not items:
            continue
        severities = [r["severity"] for r in items]
        frequency = len(items) / total
        avg_severity = sum(severities) / len(items)
        stats.append(
            {
                "theme": name,
                "type": cfg["type"],
                "items": len(items),
                "frequency": round(frequency, 3),
                "avg_severity": round(avg_severity, 2),
                "worst_severity": max(severities),
                "priority": round(frequency * avg_severity, 3),
                "examples": [r["text"] for r in items[:EXAMPLES_PER_THEME]],
            }
        )
    return sorted(stats, key=lambda s: s["priority"], reverse=True)


def write_csv(stats, path):
    fields = ["theme", "type", "items", "frequency", "avg_severity", "worst_severity", "priority"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(stats)


def table(rows):
    lines = [
        "| Theme | Items | Frequency | Avg severity | Worst | Priority |",
        "|---|---|---|---|---|---|",
    ]
    for s in rows:
        lines.append(
            f"| {s['theme']} | {s['items']} | {s['frequency']:.0%} | "
            f"{s['avg_severity']} | {s['worst_severity']} | {s['priority']} |"
        )
    return lines if rows else ["_No themes in this group._"]


def write_report(stats, total, uncategorized, source_count, skipped, path):
    fix_next = [s for s in stats if s["type"] in ("bug", "usability")]
    build_next = [s for s in stats if s["type"] == "request"]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Feedback Analysis Report",
        "",
        f"Generated {generated}. Source files: {source_count}. "
        f"Feedback items: {total}. Uncategorized: {uncategorized} "
        f"({uncategorized / total:.0%}).",
        "",
        "## Fix next (bugs and usability)",
        "",
        *table(fix_next),
        "",
        "## Build next (feature requests)",
        "",
        *table(build_next),
        "",
        "## Examples",
        "",
    ]
    for s in stats:
        lines.append(f"### {s['theme']}")
        for quote in s["examples"]:
            shortened = quote if len(quote) <= MAX_QUOTE_CHARS else quote[:MAX_QUOTE_CHARS] + "..."
            lines.append(f"- {shortened}")
        lines.append("")
    lines += ["## Skipped files", ""]
    lines += [f"- {name}: {reason}" for name, reason in skipped] or ["_None._"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    themes = json.loads(THEMES_PATH.read_text(encoding="utf-8"))
    severity_rules = {int(k): v for k, v in json.loads(SEVERITY_PATH.read_text(encoding="utf-8")).items()}

    records, skipped, source_count = [], [], 0
    for path in sorted(INPUT_DIR.iterdir()):
        if not path.is_file() or path.name.startswith(".") or path.name == "README.md":
            continue
        if path.suffix.lower() not in SUPPORTED:
            skipped.append((path.name, "unsupported format"))
            continue
        try:
            records.extend(PARSERS[path.suffix.lower()](path))
            source_count += 1
        except Exception as error:
            skipped.append((path.name, str(error)))

    if not records:
        print("No feedback found in input/. Nothing written.")
        return

    analyzed = [analyze(r, themes, severity_rules) for r in records]
    stats = theme_stats(analyzed, themes)
    uncategorized = sum(1 for r in analyzed if not r["themes"])

    write_csv(stats, OUTPUT_DIR / "themes.csv")
    write_report(stats, len(analyzed), uncategorized, source_count, skipped, OUTPUT_DIR / "report.md")
    print(f"Analyzed {len(analyzed)} items from {source_count} files. Report: output/report.md")


if __name__ == "__main__":
    main()
