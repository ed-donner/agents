from pathlib import Path

from agents import function_tool

OUTPUT_FILENAME = "job_report.pdf"


@function_tool
def write_job_report_pdf(report_text: str) -> str:

    from fpdf import FPDF

    path = Path(OUTPUT_FILENAME).resolve()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    body = report_text.replace("\r\n", "\n").strip()
    if not body:
        return "Error: report_text was empty; nothing written."

    pdf.multi_cell(0, 6, body)
    pdf.output(str(path))
    return f"Saved report to {path}"