"""Writes agent-generated code and documentation files to the output directory."""

import os
import re
import textwrap
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")


def ensure_output_dir(run_id: str) -> Path:
    """Create and return a timestamped run directory."""
    run_dir = OUTPUT_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_file(run_dir: Path, filename: str, content: str) -> Path:
    """Write content to a file inside the run directory."""
    filepath = run_dir / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def extract_code_blocks(llm_output: str) -> dict[str, str]:
    """
    Parse LLM output and extract named code blocks.
    Expects blocks in format:
        ```python filename: some_file.py
        ...code...
        ```
    Returns dict of {filename: code}.
    """
    pattern = r"```(?:\w+)?\s+filename:\s*(\S+)\n(.*?)```"
    matches = re.findall(pattern, llm_output, re.DOTALL)
    return {name.strip(): code.strip() for name, code in matches}


def make_run_id(patient_id: str) -> str:
    """Generate a unique run ID from patient ID and current timestamp."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", patient_id)
    return f"{safe_id}_{ts}"
