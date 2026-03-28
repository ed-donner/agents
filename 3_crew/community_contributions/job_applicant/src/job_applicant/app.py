#!/usr/bin/env python
"""
Gradio UI for the Multi-Agent Job Application System.

4 tabs:
1. Setup — Upload resume, configure search criteria
2. Job Matches — View matched jobs with scores
3. Applications — Track application status
4. Logs — View pipeline logs
"""

import json
import os
import threading
import gradio as gr

from .main import run as run_pipeline
from .state import ApplicationStateManager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_BUFFER = []


def capture_log(msg: str):
    LOG_BUFFER.append(msg)


def run_job_search(
    resume_file,
    keywords: str,
    locations: str,
    platforms: list,
    job_types: list,
    min_score: float,
):
    """Run the full pipeline from the Gradio UI."""
    global LOG_BUFFER
    LOG_BUFFER = []

    if resume_file is None:
        return "Please upload your resume first.", "", ""

    # Save uploaded resume
    resume_dir = os.path.join(BASE_DIR, "resumes")
    os.makedirs(resume_dir, exist_ok=True)
    resume_path = os.path.join(resume_dir, os.path.basename(resume_file.name))

    with open(resume_path, "wb") as f:
        with open(resume_file.name, "rb") as src:
            f.write(src.read())

    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    location_list = [l.strip() for l in locations.split(",") if l.strip()]

    if not keyword_list:
        return "Please enter at least one search keyword.", "", ""

    if not location_list:
        location_list = ["Remote"]

    if not platforms:
        platforms = ["linkedin", "indeed", "glassdoor", "ziprecruiter"]

    if not job_types:
        job_types = ["Full-time"]

    try:
        stats = run_pipeline(
            resume_path=resume_path,
            keywords=keyword_list,
            locations=location_list,
            platforms=platforms,
            job_types=job_types,
            min_match_score=min_score,
        )

        status_msg = (
            f"Pipeline complete!\n\n"
            f"Jobs discovered: {stats['total_jobs_discovered']}\n"
            f"Applications submitted: {stats['submitted']}\n"
            f"Applications failed: {stats['failed']}\n"
            f"Applications blocked: {stats['blocked']}\n"
            f"Platforms: {json.dumps(stats['by_platform'], indent=2)}"
        )

        return status_msg, get_matched_jobs_table(), get_applications_table()

    except Exception as e:
        return f"Error: {str(e)}", "", ""


def get_matched_jobs_table():
    """Load matched jobs from the state database."""
    state = ApplicationStateManager(db_path=os.path.join(BASE_DIR, "output", "applications.db"))
    jobs = state.get_matched_jobs()

    if not jobs:
        return "No matched jobs found yet. Run a search first."

    lines = ["| Score | Title | Company | Location | Platform | Recommendation |",
             "|-------|-------|---------|----------|----------|----------------|"]

    for job in jobs:
        score = f"{job.get('score', 0):.2f}" if job.get('score') else "N/A"
        lines.append(
            f"| {score} | {job.get('title', 'N/A')} | {job.get('company', 'N/A')} | "
            f"{job.get('location', 'N/A')} | {job.get('platform', 'N/A')} | "
            f"{job.get('recommendation', 'N/A')} |"
        )

    return "\n".join(lines)


def get_applications_table():
    """Load application results from the state database."""
    state = ApplicationStateManager(db_path=os.path.join(BASE_DIR, "output", "applications.db"))
    apps = state.get_all_applications()

    if not apps:
        return "No applications submitted yet."

    lines = ["| Status | Title | Company | Platform | Date | Error |",
             "|--------|-------|---------|----------|------|-------|"]

    for app in apps:
        status_emoji = {"submitted": "✅", "failed": "❌", "blocked": "🚫"}.get(
            app.get("status", ""), "❓"
        )
        error = app.get("error_message", "") or ""
        if len(error) > 50:
            error = error[:50] + "..."

        lines.append(
            f"| {status_emoji} {app.get('status', 'N/A')} | {app.get('title', 'N/A')} | "
            f"{app.get('company', 'N/A')} | {app.get('platform', 'N/A')} | "
            f"{app.get('applied_at', 'N/A')[:10]} | {error} |"
        )

    return "\n".join(lines)


def get_logs():
    """Get current log buffer."""
    if not LOG_BUFFER:
        return "No logs yet. Run a search to see activity."
    return "\n".join(LOG_BUFFER[-200:])


def get_stats():
    """Get summary statistics."""
    state = ApplicationStateManager(db_path=os.path.join(BASE_DIR, "output", "applications.db"))
    stats = state.get_stats()
    return json.dumps(stats, indent=2)


def create_app():
    """Create the Gradio application."""

    with gr.Blocks(
        title="Job Application Agent",
        theme=gr.themes.Soft(),
    ) as app:
        gr.Markdown(
            "# 🎯 Multi-Agent Job Application System\n"
            "Automatically search, match, tailor, and apply to jobs across multiple platforms."
        )

        with gr.Tabs():
            # ── Tab 1: Setup ────────────────────────────────
            with gr.Tab("Setup"):
                gr.Markdown("### Configure your job search")

                with gr.Row():
                    with gr.Column(scale=1):
                        resume_upload = gr.File(
                            label="Upload Resume (PDF or DOCX)",
                            file_types=[".pdf", ".docx", ".doc", ".txt"],
                        )
                        keywords_input = gr.Textbox(
                            label="Search Keywords (comma-separated)",
                            placeholder="software engineer, python developer, backend engineer",
                            value="software engineer, python developer",
                        )
                        locations_input = gr.Textbox(
                            label="Locations (comma-separated)",
                            placeholder="Remote, San Francisco CA, New York NY",
                            value="Remote",
                        )

                    with gr.Column(scale=1):
                        platforms_input = gr.CheckboxGroup(
                            choices=["linkedin", "indeed", "glassdoor", "ziprecruiter"],
                            label="Platforms",
                            value=["linkedin", "indeed", "glassdoor", "ziprecruiter"],
                        )
                        job_types_input = gr.CheckboxGroup(
                            choices=["Full-time", "Part-time", "Contract", "Internship"],
                            label="Job Types",
                            value=["Full-time"],
                        )
                        min_score_input = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            step=0.05,
                            value=0.5,
                            label="Minimum Match Score",
                        )

                run_button = gr.Button("🚀 Start Job Search & Auto-Apply", variant="primary", size="lg")
                status_output = gr.Textbox(label="Status", lines=8, interactive=False)

            # ── Tab 2: Matched Jobs ─────────────────────────
            with gr.Tab("Job Matches"):
                gr.Markdown("### Matched Jobs (ranked by score)")
                refresh_matches_btn = gr.Button("🔄 Refresh")
                matches_output = gr.Markdown(value="No matched jobs yet. Run a search first.")

            # ── Tab 3: Applications ─────────────────────────
            with gr.Tab("Applications"):
                gr.Markdown("### Application Status Tracker")
                refresh_apps_btn = gr.Button("🔄 Refresh")
                apps_output = gr.Markdown(value="No applications yet.")
                stats_output = gr.JSON(label="Statistics")

            # ── Tab 4: Logs ─────────────────────────────────
            with gr.Tab("Logs"):
                gr.Markdown("### Pipeline Logs")
                refresh_logs_btn = gr.Button("🔄 Refresh Logs")
                logs_output = gr.Textbox(
                    label="Activity Log",
                    lines=25,
                    interactive=False,
                    value="No logs yet.",
                )

        # ── Event Handlers ──────────────────────────────────
        run_button.click(
            fn=run_job_search,
            inputs=[
                resume_upload,
                keywords_input,
                locations_input,
                platforms_input,
                job_types_input,
                min_score_input,
            ],
            outputs=[status_output, matches_output, apps_output],
        )

        refresh_matches_btn.click(fn=get_matched_jobs_table, outputs=[matches_output])
        refresh_apps_btn.click(
            fn=lambda: (get_applications_table(), get_stats()),
            outputs=[apps_output, stats_output],
        )
        refresh_logs_btn.click(fn=get_logs, outputs=[logs_output])

    return app


def launch():
    """Launch the Gradio app."""
    app = create_app()
    app.launch(share=False)


if __name__ == "__main__":
    launch()
