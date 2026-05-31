import os
from pathlib import Path

from agents import function_tool

OUTPUT_FILENAME = "job_report.pdf"


def _latin1_safe(text: str) -> str:
    """Helvetica/core fonts only support Latin-1; strip/replace the rest."""
    return text.encode("latin-1", errors="replace").decode("latin-1")


@function_tool
def write_job_report_pdf(report_text: str) -> str:
    """Write job_report.pdf. Respects JOB_REPORT_OUTPUT_DIR (set by Manager for each run)."""

    from fpdf import FPDF

    base = Path(os.environ.get("JOB_REPORT_OUTPUT_DIR", ".")).resolve()
    base.mkdir(parents=True, exist_ok=True)
    path = (base / OUTPUT_FILENAME).resolve()

    body = _latin1_safe(report_text.replace("\r\n", "\n").strip())
    if not body:
        return "Error: report_text was empty; nothing written."

    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, body)
        pdf.output(str(path))
    except Exception as e:
        return f"Error writing PDF: {e}"

    return f"Saved report to {path}"