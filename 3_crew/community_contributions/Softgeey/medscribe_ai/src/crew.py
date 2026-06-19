"""
MedScribe AI Crew Orchestrator
Runs the full autonomous pipeline:
  1. Clinical Analyst    — extract structured data from raw notes
  2. Discharge Planner   — generate discharge plan
  3. Medical Writer      — compose the discharge summary document
  4. QA Reviewer         — audit quality and flag issues
  5. Code Engineer       — produce deployable Python implementation

Results are saved to the output/ directory under a unique run ID.
"""

import json
import logging
from pathlib import Path

from src.agents import (
    clinical_analyst,
    discharge_planner,
    medical_writer,
    qa_reviewer,
    code_engineer,
)
from src.tasks.task_runner import run_task, TaskResult
from src.utils.file_writer import (
    ensure_output_dir,
    write_file,
    extract_code_blocks,
    make_run_id,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def _safe_parse_json(text: str) -> dict:
    """Attempt to parse JSON, returning a dict with error info on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to extract JSON from within a larger text block
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {"parse_error": "Could not parse JSON from agent output", "raw": text[:500]}


def _build_crew_report(run_id: str, tasks: list[TaskResult], run_dir: Path) -> str:
    """Compile a human-readable crew execution report."""
    lines = [
        "MEDSCRIBE AI — CREW EXECUTION REPORT",
        "=" * 45,
        f"Run ID : {run_id}",
        f"Output : {run_dir}",
        "",
    ]
    for t in tasks:
        status = "✓ PASS" if t.success else "✗ FAIL"
        lines.append(f"[{status}] {t.task_name} ({t.agent_name})")
        if not t.success:
            lines.append(f"         Error: {t.error}")
    lines.append("")
    lines.append("All files written to output directory.")
    return "\n".join(lines)


def run_crew(patient_data: str, patient_id: str = "PATIENT") -> dict:
    """
    Execute the full MedScribe AI agent pipeline.

    Args:
        patient_data: Raw clinical notes / patient record text
        patient_id:   Identifier used for the output folder name

    Returns:
        A result dict with keys: run_id, run_dir, tasks, files, report, success
    """
    run_id = make_run_id(patient_id)
    run_dir = ensure_output_dir(run_id)
    completed_tasks: list[TaskResult] = []
    files_written: list[str] = []

    log.info("=== MedScribe AI Crew started | run_id=%s ===", run_id)

    # ── Task 1: Extract structured clinical data ──────────────────────────────
    log.info("Task 1/5 — Clinical Analyst: extracting structured data...")
    t1 = run_task("Extract Clinical Data", "Clinical Analyst", clinical_analyst.run, patient_data)
    completed_tasks.append(t1)

    if not t1.success:
        log.error("Clinical Analyst failed: %s", t1.error)
        return _abort(run_id, run_dir, completed_tasks, t1.error)

    patient_json = t1.output
    write_file(run_dir, "01_clinical_data.json", patient_json)
    files_written.append("01_clinical_data.json")
    log.info("Task 1 complete.")

    # ── Task 2: Generate discharge plan ───────────────────────────────────────
    log.info("Task 2/5 — Discharge Planner: building discharge plan...")
    t2 = run_task("Generate Discharge Plan", "Discharge Planner", discharge_planner.run, patient_json)
    completed_tasks.append(t2)

    if not t2.success:
        log.error("Discharge Planner failed: %s", t2.error)
        return _abort(run_id, run_dir, completed_tasks, t2.error)

    plan_json = t2.output
    write_file(run_dir, "02_discharge_plan.json", plan_json)
    files_written.append("02_discharge_plan.json")
    log.info("Task 2 complete.")

    # ── Task 3: Write the discharge summary ───────────────────────────────────
    log.info("Task 3/5 — Medical Writer: composing discharge summary...")
    t3 = run_task("Write Discharge Summary", "Medical Writer", medical_writer.run, patient_json, plan_json)
    completed_tasks.append(t3)

    if not t3.success:
        log.error("Medical Writer failed: %s", t3.error)
        return _abort(run_id, run_dir, completed_tasks, t3.error)

    summary_text = t3.output
    write_file(run_dir, "03_discharge_summary.txt", summary_text)
    files_written.append("03_discharge_summary.txt")
    log.info("Task 3 complete.")

    # ── Task 4: QA review ─────────────────────────────────────────────────────
    log.info("Task 4/5 — QA Reviewer: auditing discharge summary...")
    t4 = run_task("QA Review", "QA Reviewer", qa_reviewer.run, summary_text)
    completed_tasks.append(t4)

    if not t4.success:
        log.error("QA Reviewer failed: %s", t4.error)
        return _abort(run_id, run_dir, completed_tasks, t4.error)

    qa_report = t4.output
    write_file(run_dir, "04_qa_report.json", qa_report)
    files_written.append("04_qa_report.json")

    qa_data = _safe_parse_json(qa_report)
    quality_score = qa_data.get("quality_score", 0)
    approved = qa_data.get("approved", False)
    log.info("Task 4 complete. QA Score=%s Approved=%s", quality_score, approved)

    # ── Task 5: Generate deployable code ──────────────────────────────────────
    log.info("Task 5/5 — Code Engineer: generating Python implementation...")
    t5 = run_task("Generate Code", "Code Engineer", code_engineer.run, patient_json, summary_text, qa_report)
    completed_tasks.append(t5)

    if not t5.success:
        log.error("Code Engineer failed: %s", t5.error)
        return _abort(run_id, run_dir, completed_tasks, t5.error)

    code_output = t5.output
    write_file(run_dir, "05_generated_code_raw.txt", code_output)
    files_written.append("05_generated_code_raw.txt")

    # Extract and save individual code files
    code_blocks = extract_code_blocks(code_output)
    for filename, code in code_blocks.items():
        write_file(run_dir, filename, code)
        files_written.append(filename)
        log.info("Code file written: %s", filename)

    log.info("Task 5 complete.")

    # ── Crew report ───────────────────────────────────────────────────────────
    report = _build_crew_report(run_id, completed_tasks, run_dir)
    write_file(run_dir, "crew_report.txt", report)
    files_written.append("crew_report.txt")

    log.info("=== MedScribe AI Crew finished | run_id=%s ===", run_id)

    return {
        "success": True,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "tasks": [
            {
                "name": t.task_name,
                "agent": t.agent_name,
                "success": t.success,
                "error": t.error,
            }
            for t in completed_tasks
        ],
        "files": files_written,
        "report": report,
        "discharge_summary": summary_text,
        "qa_score": quality_score,
        "qa_approved": approved,
    }


def _abort(run_id: str, run_dir: Path, tasks: list[TaskResult], error: str) -> dict:
    """Return a structured failure response."""
    return {
        "success": False,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "tasks": [
            {
                "name": t.task_name,
                "agent": t.agent_name,
                "success": t.success,
                "error": t.error,
            }
            for t in tasks
        ],
        "files": [],
        "report": f"Pipeline aborted: {error}",
        "discharge_summary": "",
        "qa_score": 0,
        "qa_approved": False,
    }
