#!/usr/bin/env python3
"""
dump_notebook_cells.py
Export the contents (and optionally outputs) of cells from a Jupyter .ipynb file into a text or JSON file.

Usage:
  python dump_notebook_cells.py path/to/notebook.ipynb --output out.txt
  python dump_notebook_cells.py path/to/notebook.ipynb --include-outputs --output out.json --as-json
"""

import argparse
import json
import sys
from pathlib import Path
import nbformat


def extract_output_text(output) -> str:
    otype = output.get("output_type")
    if otype == "stream":
        return output.get("text", "")
    elif otype in ("execute_result", "display_data"):
        data = output.get("data", {})
        if "text/plain" in data:
            return str(data["text/plain"])
        if data:
            first_mime = next(iter(data))
            return f"[{first_mime}] {data[first_mime]}"
        return ""
    elif otype == "error":
        ename = output.get("ename", "Error")
        evalue = output.get("evalue", "")
        tb = "\n".join(output.get("traceback", []))
        return f"{ename}: {evalue}\n{tb}"
    return json.dumps(output, ensure_ascii=False)


def dump_pretty(nb, include_outputs: bool) -> str:
    lines = []
    for idx, cell in enumerate(nb.get("cells", []), start=1):
        ctype = cell.get("cell_type", "unknown")
        lines.append(f"\n=== Cell {idx} ({ctype}) ===")
        lines.append(cell.get("source", "").rstrip("\n"))

        if include_outputs and ctype == "code":
            outputs = cell.get("outputs", [])
            if outputs:
                lines.append("\n--- Outputs ---")
                for j, out in enumerate(outputs, start=1):
                    text = extract_output_text(out)
                    lines.append(f"[{j}] {text.rstrip()}")
            else:
                lines.append("\n--- Outputs ---\n[no outputs]")
    return "\n".join(lines)


def dump_json(nb, include_outputs: bool) -> str:
    out = []
    for idx, cell in enumerate(nb.get("cells", []), start=1):
        item = {
            "index": idx,
            "type": cell.get("cell_type", "unknown"),
            "source": cell.get("source", ""),
        }
        if include_outputs and cell.get("cell_type") == "code":
            raw_outputs = cell.get("outputs", [])
            item["outputs"] = [extract_output_text(o) for o in raw_outputs]
        out.append(item)
    return json.dumps(out, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description="Export Jupyter notebook cells.")
    ap.add_argument("notebook", type=Path, help="Path to .ipynb file")
    ap.add_argument("--include-outputs", action="store_true", help="Also include outputs")
    ap.add_argument("--as-json", action="store_true", help="Export as structured JSON")
    ap.add_argument("--output", type=Path, help="Output file (default: stdout)")
    args = ap.parse_args()

    if not args.notebook.exists():
        sys.exit(f"Error: File not found: {args.notebook}")

    nb = nbformat.read(args.notebook, as_version=4)

    if args.as_json:
        content = dump_json(nb, args.include_outputs)
    else:
        content = dump_pretty(nb, args.include_outputs)

    if args.output:
        args.output.write_text(content, encoding="utf-8")
        print(f"Exported notebook cells to {args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()