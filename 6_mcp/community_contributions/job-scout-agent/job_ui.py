"""
job_ui.py — Iteration 2+3: Gradio UI to review ranked jobs, select some, and
generate cover letters (as downloadable PDFs) directly for the selected jobs.

Usage:
    uv run python job_ui.py

Reads jobs_ranked.json (produced by job_evaluator.py) and displays each job as a
bordered card with a checkbox placed directly beside it. The user checks the jobs
they want, then clicks "Generate Cover Letters for Selected" — this saves the
checked jobs to jobs_selected.json and immediately runs the cover letter pipeline
(cover_letter.py) ONLY for those jobs, then offers each PDF as a download link.
"""

import asyncio
import json
from pathlib import Path

import gradio as gr

from cover_letter import (
    generate_letter_for_job,
    load_profile,
    render_cover_letter_pdf,
    slugify,
    OUTPUT_DIR,
)

RANKED_PATH = Path("jobs_ranked.json")
SELECTED_PATH = Path("jobs_selected.json")


def load_ranked_jobs(path: Path = RANKED_PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def format_job_body(job: dict) -> str:
    """Render the descriptive part of a job (everything except the checkbox)."""
    title = job.get("title", "Untitled")
    company = job.get("company", "Unknown company")
    location = job.get("location", "N/A")
    salary = job.get("salary") or "Not specified"
    url = job.get("url", "")
    score = job.get("match_score", "N/A")
    short_desc = job.get("short_description", "")
    reason = job.get("match_reason", "")
    requirements = job.get("key_requirements", [])
    missing = job.get("missing_requirements", [])

    req_lines = "\n".join(f"- {r}" for r in requirements) if requirements else "_Not specified_"

    missing_block = ""
    if missing:
        missing_lines = "\n".join(f"- {r}" for r in missing)
        missing_block = f"""
**⚠️ Missing must-haves:**
{missing_lines}
"""

    return f"""### {title}  `[{score}/10]`
**{company}** &nbsp;|&nbsp; 📍 {location} &nbsp;|&nbsp; 💰 {salary}

{short_desc}

**Why this matches:** {reason}
{missing_block}
**Key requirements:**
{req_lines}

🔗 [View posting]({url})
"""


CARD_CSS = """
.job-card {
    border: 1px solid #e0e0e0 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.job-checkbox-col,
.job-checkbox-col .block,
.job-checkbox-col .form,
.job-checkbox-col > div,
.job-checkbox-col label,
.job-checkbox-col fieldset,
.job-checkbox-col span {
    --block-background-fill: transparent !important;
    --background-fill-primary: transparent !important;
    --border-color-primary: transparent !important;
    --block-border-width: 0px !important;
    --block-shadow: none !important;
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.job-checkbox-col {
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 18px !important;
}
"""


def save_selected_jobs(selected_jobs: list[dict]) -> None:
    SELECTED_PATH.write_text(
        json.dumps(selected_jobs, indent=2, ensure_ascii=False), encoding="utf-8"
    )


async def generate_letters_for_jobs(jobs: list[dict]) -> list[str]:
    """Run the cover letter pipeline for exactly the given jobs. Returns list of PDF paths.

    No external scraping tool is needed: each job's full_description (captured at Scout
    time) is passed inline in the prompt by cover_letter.py, so this is a pure sequence
    of LLM calls with no MCP server/Firecrawl dependency."""
    profile = load_profile()
    OUTPUT_DIR.mkdir(exist_ok=True)

    pdf_paths = []

    for job in jobs:
        letter = await generate_letter_for_job(job, profile)
        filename = f"{slugify(job.get('company',''))}_{slugify(job.get('title',''))}.pdf"
        out_path = OUTPUT_DIR / filename
        render_cover_letter_pdf(letter, job, out_path)
        pdf_paths.append(str(out_path))

    return pdf_paths


def on_generate_clicked(checkbox_values: list[bool], jobs: list[dict]):
    """Gradio click handler: filter to checked jobs, save selection, generate PDFs."""
    selected_jobs = [job for job, checked in zip(jobs, checkbox_values) if checked]

    if not selected_jobs:
        return "⚠️ No jobs selected. Please check at least one job above.", []

    save_selected_jobs(selected_jobs)

    status_lines = [f"⏳ Generating cover letters for {len(selected_jobs)} job(s)...\n"]
    for j in selected_jobs:
        status_lines.append(f"- {j.get('title')} @ {j.get('company')}")

    pdf_paths = asyncio.run(generate_letters_for_jobs(selected_jobs))

    status_lines.append(f"\n✅ Generated {len(pdf_paths)} cover letter(s). Download below.")
    return "\n".join(status_lines), pdf_paths


def build_app() -> gr.Blocks:
    jobs = load_ranked_jobs()

    with gr.Blocks(title="Job Scout — Review & Select", css=CARD_CSS) as demo:
        gr.Markdown("# 🔍 Job Scout — Review & Select")
        gr.Markdown(
            "Review the ranked job matches below. Check the ones you'd like a "
            "cover letter for, then click **Generate Cover Letters for Selected**."
        )

        checkboxes = []

        if not jobs:
            gr.Markdown(
                f"⚠️ No jobs found in `{RANKED_PATH}`. Run the Scout → Prefilter → "
                "Evaluator pipeline first (Iteration 1)."
            )
        else:
            for i, job in enumerate(jobs, 1):
                with gr.Group(elem_classes=["job-card"]):
                    with gr.Row(equal_height=False):
                        with gr.Column(scale=1, min_width=50, elem_classes=["job-checkbox-col"]):
                            cb = gr.Checkbox(label=f"#{i}", value=False)
                        with gr.Column(scale=12):
                            gr.Markdown(format_job_body(job))
                    checkboxes.append(cb)

            generate_btn = gr.Button("✉️ Generate Cover Letters for Selected", variant="primary")
            status_box = gr.Markdown()
            download_files = gr.File(label="Download cover letters", file_count="multiple")

            generate_btn.click(
                fn=lambda *vals: on_generate_clicked(list(vals), jobs),
                inputs=checkboxes,
                outputs=[status_box, download_files],
            )

    return demo


def main():
    demo = build_app()
    demo.launch()


if __name__ == "__main__":
    main()
