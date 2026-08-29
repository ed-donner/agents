


### Python extractor (`extract_code.py`)

import os
import re

MARKDOWN_FILE = "crew2_output/flutter.md"
OUTPUT_ROOT = "./mobile_repo"

# Find sections that start with '### <path>' followed by content until the next ### or EOF
section_pattern = re.compile(r"###\s+([^\n]+)\n(.*?)(?=\n###\s+[^\n]+\n|\Z)", re.DOTALL)
# Matches bold headings like: **index.js**
bold_heading_pattern = re.compile(r"^\*\*(.+?)\*\*\s*$", re.MULTILINE)
code_block_pattern = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)


def normalize_path(p: str) -> str:
    p = p.strip()
    # Remove any leading slashes and normalize separators
    if p.startswith("/") or p.startswith("\\"):
        p = p[1:]
    return os.path.normpath(p)


def extract_and_write(markdown: str):
    # Try '### path' sections first
    matches = section_pattern.findall(markdown)
    if matches:
        for path, body in matches:
            file_path = normalize_path(path)
            print(f"Processing section for path: {file_path}")

            code_match = code_block_pattern.search(body)
            if not code_match:
                print(f"  No code block found for section '{file_path}', skipping.")
                continue

            code = code_match.group(1).rstrip('\n')

            full_path = os.path.join(OUTPUT_ROOT, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as out:
                out.write(code)

            print(f"  Written: {full_path}")
        return

    # Fallback: look for bold headings like **index.js** followed by a code block
    for m in bold_heading_pattern.finditer(markdown):
        path = m.group(1).strip()
        file_path = normalize_path(path)
        start_pos = m.end()
        # search for the next code block after the heading
        code_match = code_block_pattern.search(markdown, pos=start_pos)
        if not code_match:
            print(f"  No code block found for bold section '{file_path}', skipping.")
            continue

        code = code_match.group(1).rstrip('\n')
        full_path = os.path.join(OUTPUT_ROOT, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as out:
            out.write(code)
        print(f"  Written: {full_path}")


if __name__ == "__main__":
    if not os.path.exists(MARKDOWN_FILE):
        print(f"Markdown file not found: {MARKDOWN_FILE}")
        raise SystemExit(1)

    with open(MARKDOWN_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    extract_and_write(content)
