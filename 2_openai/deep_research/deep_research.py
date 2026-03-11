import importlib
import json
import os
import tempfile
import zipfile
from datetime import datetime

import gradio as gr
from dotenv import load_dotenv

from agents import Runner
from email_agent import email_agent
from research_manager import ResearchManager
from guardrails import run_guardrails

load_dotenv(override=True)

manager = ResearchManager()

HISTORY_FILE = "deep_research_history.jsonl"


def _extract_report_from_output(text: str) -> str:
    if not text:
        return ""
    marker = "\n---\n\n# Report"
    if marker in text:
        idx = text.find(marker)
        return text[idx + len(marker) :].lstrip()
    if "# Report" in text:
        idx = text.find("# Report")
        return text[idx:].strip()
    return text.strip()


def _extract_sources(report_markdown: str) -> list[dict]:
    lines = (report_markdown or "").splitlines()
    in_sources = False
    sources: list[dict] = []

    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith("## sources"):
            in_sources = True
            continue
        if in_sources:
            if not stripped:
                continue
            if stripped.startswith("## "):
                break
            idx = None
            if stripped.startswith("["):
                end = stripped.find("]")
                if end > 1:
                    try:
                        idx = int(stripped[1:end])
                    except Exception:
                        idx = None
            sources.append({"index": idx, "text": stripped})
    return sources


def _append_history_entry(entry: dict) -> None:
    try:
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            json.dump(entry, f)
            f.write("\n")
    except Exception:
        pass


def _read_history_entries() -> list[dict]:
    if not os.path.exists(HISTORY_FILE):
        return []
    entries: list[dict] = []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return []
    return entries


async def send_report_email(report_markdown: str, recipient_email: str) -> str:
    report_markdown = (report_markdown or "").strip()
    if not report_markdown:
        return "No report available to email yet. Run deep research first."

    parts: list[str] = []
    recipient_email = (recipient_email or "").strip()
    if recipient_email:
        parts.append(f"Recipient email: {recipient_email}")
    parts.append(report_markdown)
    prompt = "\n\n".join(parts)

    try:
        await Runner.run(email_agent, prompt)
        return "Report emailed successfully."
    except Exception as e:
        return f"Failed to send email: {e}"


def create_pdf_from_report(report_markdown: str) -> str:
    report_markdown = (report_markdown or "").strip()
    if not report_markdown:
        raise ValueError("No report available to download yet. Run deep research first."
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    pagesizes = importlib.import_module("reportlab.lib.pagesizes")
    pdfgen_canvas = importlib.import_module("reportlab.pdfgen.canvas")
    letter = pagesizes.letter
    canvas_cls = pdfgen_canvas.Canvas

    c = canvas_cls(tmp.name, pagesize=letter)
    width, height = letter
    x_margin, y_margin = 72, 72
    y = height - y_margin

    line_height = 14
    max_width_chars = 100

    for raw_line in report_markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            y -= line_height
            continue

        # Wrap long lines instead of truncating so the full report appears.
        while line:
            if y < y_margin:
                c.showPage()
                y = height - y_margin
            chunk = line[:max_width_chars]
            c.drawString(x_margin, y, chunk)
            y -= line_height
            line = line[max_width_chars:]

    c.save()
    tmp.close()
    return tmp.name


def export_report_bundle(report_markdown: str) -> str:
    """Create a ZIP bundle with the markdown report, PDF and sources.json."""
    report_markdown = (report_markdown or "").strip()
    if not report_markdown:
        raise ValueError("No report available to export yet. Run deep research first.")

    # Prepare temporary files
    tmp_dir = tempfile.mkdtemp(prefix="deep_research_bundle_")
    md_path = os.path.join(tmp_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_markdown)

    # Reuse PDF generator; ignore failures
    pdf_path = None
    try:
        pdf_path = create_pdf_from_report(report_markdown)
    except Exception:
        pdf_path = None

    sources = _extract_sources(report_markdown)
    sources_path = os.path.join(tmp_dir, "sources.json")
    with open(sources_path, "w", encoding="utf-8") as f:
        json.dump(sources, f, ensure_ascii=False, indent=2)

    bundle_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(md_path, "report.md")
        zf.write(sources_path, "sources.json")
        if pdf_path and os.path.exists(pdf_path):
            zf.write(pdf_path, "report.pdf")

    return bundle_path


async def get_clarifying_questions(query: str):
    """Phase 1: guardrails + clarifying questions. Everything except the Get button stays hidden until this succeeds."""
    query = (query or "").strip()
    if not query:
        # Keep everything else hidden.
        hidden = gr.update(visible=False)
        return (
            "Please enter a research topic first.",
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
        )
    gr_result = run_guardrails(query, answers=[], check_pii=True, check_intent=True, check_length=True)
    if not gr_result.passed:
        hidden = gr.update(visible=False)
        return (
            f"**Input guardrail:** {gr_result.message}",
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
        )
    try:
        questions = await manager.get_clarifying_questions(query)
        q1, q2, q3 = (questions + [""] * 3)[:3]
        # Show the rest of the form only after successful clarification.
        return (
            gr.update(
                value="**Answer these to focus the research (optional). You can leave blanks and click Run.**",
                visible=True,
            ),
            gr.update(value=q1, visible=True),
            gr.update(value=q2, visible=True),
            gr.update(value=q3, visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
            gr.update(visible=True),
        )
    except Exception as e:
        hidden = gr.update(visible=False)
        return (
            f"Could not generate questions: {e}",
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
            hidden,
        )


async def run_research(
    query: str,
    q1: str,
    q2: str,
    q3: str,
    a1: str,
    a2: str,
    a3: str,
    recipient_email: str,
):
    query = (query or "").strip()
    if not query:
        yield "Please enter a research topic.", ""
        return
    questions = [q1, q2, q3]
    answers = [a1, a2, a3]
    refined = manager.refine_query_with_answers(
        query, questions, answers, recipient_email=(recipient_email or "").strip() or None
    )

    last_chunk = ""
    async for chunk in manager.run(refined):
        last_chunk = chunk
        # Stream status + report to UI; keep advanced options hidden until done.
        yield chunk, "", gr.update(visible=False)

    # After the stream finishes, store just the report body for email/PDF and history.
    report_only = _extract_report_from_output(last_chunk)

    entry = {
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "query": query,
        "questions": questions,
        "answers": answers,
        "recipient_email": (recipient_email or "").strip() or None,
        "report_markdown": report_only,
    }
    _append_history_entry(entry)

    # Final yield shows full report and reveals advanced options.
    yield last_chunk, report_only, gr.update(visible=True)


def refresh_history():
    """Load run history summaries for the UI dropdown and state."""
    entries = _read_history_entries()
    labels: list[str] = []
    for i, e in enumerate(entries):
        ts = e.get("created_at", "") or ""
        q = (e.get("query", "") or "").replace("\n", " ")
        short_q = (q[:80] + "…") if len(q) > 80 else q
        labels.append(f"{i + 1}. {ts} – {short_q}")
    return labels, entries


def load_history_item(selected_label: str, entries: list[dict]) -> tuple[str, str]:
    """Given a selected history label and entries state, load its report into the UI."""
    if not selected_label or not entries:
        return "", ""
    try:
        index_str = selected_label.split(".", 1)[0]
        index = int(index_str) - 1
    except Exception:
        return "", ""
    if index < 0 or index >= len(entries):
        return "", ""
    report_text = (entries[index].get("report_markdown") or "").strip()
    return report_text, report_text


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research") as ui:
    gr.Markdown("# Deep Research")
    gr.Markdown(
        "Enter a topic, get 3 clarifying questions (optional to answer), and optionally enter an email to receive the report. Then run."
    )

    query_textbox = gr.Textbox(
        label="What would you like to research?",
        placeholder="e.g. Impact of AI on legal practice in the UK",
    )
    get_questions_btn = gr.Button("Get clarifying questions", variant="primary")

    clar_section = gr.Markdown(value="", label="Clarifications", visible=False)
    q1_box = gr.Textbox(label="Question 1", interactive=False, visible=False)
    q2_box = gr.Textbox(label="Question 2", interactive=False, visible=False)
    q3_box = gr.Textbox(label="Question 3", interactive=False, visible=False)
    a1_box = gr.Textbox(label="Your answer (optional)", visible=False)
    a2_box = gr.Textbox(label="Your answer (optional)", visible=False)
    a3_box = gr.Textbox(label="Your answer (optional)", visible=False)

    recipient_email_box = gr.Textbox(
        label="Recipient email (optional — report will be sent here after research; leave blank to skip email or use default)",
        placeholder="e.g. colleague@example.com",
        visible=False,
    )

    run_btn = gr.Button("Run deep research", variant="secondary", visible=False)
    report = gr.Markdown(label="Report")
    report_state = gr.State("")

    with gr.Group(visible=False) as post_section:
        send_email_btn = gr.Button("Send report as email")
        download_pdf_btn = gr.Button("Download report as PDF")
        export_bundle_btn = gr.Button("Download report bundle (ZIP)")
        email_status = gr.Markdown(label="Email status")
        pdf_file = gr.File(label="Report PDF")
        bundle_file = gr.File(label="Report bundle (.zip)")

        review_btn = gr.Button("Generate team review checklist")
        review_checklist = gr.Markdown(label="Team review checklist")

        history_state = gr.State([])
        history_refresh_btn = gr.Button("Refresh history")
        history_dropdown = gr.Dropdown(label="Previous runs", choices=[], interactive=True)
        history_load_btn = gr.Button("Load selected run")

    get_questions_btn.click(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=[
            clar_section,
            q1_box,
            q2_box,
            q3_box,
            a1_box,
            a2_box,
            a3_box,
            recipient_email_box,
            run_btn,
        ],
    )
    run_btn.click(
        fn=run_research,
        inputs=[
            query_textbox,
            q1_box,
            q2_box,
            q3_box,
            a1_box,
            a2_box,
            a3_box,
            recipient_email_box,
        ],
        outputs=[report, report_state, post_section],
    )
    query_textbox.submit(
        fn=get_clarifying_questions,
        inputs=query_textbox,
        outputs=[
            clar_section,
            q1_box,
            q2_box,
            q3_box,
            a1_box,
            a2_box,
            a3_box,
            recipient_email_box,
            run_btn,
        ],
    )

    send_email_btn.click(
        fn=send_report_email,
        inputs=[report_state, recipient_email_box],
        outputs=email_status,
    )

    download_pdf_btn.click(
        fn=create_pdf_from_report,
        inputs=report_state,
        outputs=pdf_file,
    )

    export_bundle_btn.click(
        fn=export_report_bundle,
        inputs=report_state,
        outputs=bundle_file,
    )

    review_btn.click(
        fn=lambda report_text: (
            "### Team review checklist\n\n"
            "- [ ] Does the report accurately reflect the original research question and any clarifications?\n"
            "- [ ] Are all key conclusions traceable to specific cited sources (with [N] references)?\n"
            "- [ ] Is there sufficient diversity of sources (independent sites, jurisdictions, and viewpoints)?\n"
            "- [ ] Are any legal or risk-related statements clearly framed as high-level analysis rather than formal advice?\n"
            "- [ ] Are obvious conflicts of interest, limitations, or assumptions disclosed?\n"
            "- [ ] Are recommended actions practical, time-bound, and clearly prioritized?\n"
        )
        if (report_text or "").strip()
        else "Run deep research first to generate a report, then create a checklist.",
        inputs=report_state,
        outputs=review_checklist,
    )

    history_refresh_btn.click(
        fn=refresh_history,
        inputs=None,
        outputs=[history_dropdown, history_state],
    )

    history_load_btn.click(
        fn=load_history_item,
        inputs=[history_dropdown, history_state],
        outputs=[report, report_state],
    )

if __name__ == "__main__":
    # share=True creates a public gradio.live link so others can try your app
    ui.launch(inbrowser=True, share=True)
