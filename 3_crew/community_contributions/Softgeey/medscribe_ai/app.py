"""
MedScribe AI — Flask Web Application
Provides a simple UI for hospital staff to submit patient notes
and receive fully generated discharge summary packages.
"""

import json
import threading
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory

from src.config import get_flask_secret, is_debug
from src.crew import run_crew

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = get_flask_secret()

# Track active jobs in memory (sufficient for single-server deployment)
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _run_crew_async(job_id: str, patient_data: str, patient_id: str) -> None:
    """Run the crew pipeline in a background thread and store the result."""
    result = run_crew(patient_data, patient_id)
    with _jobs_lock:
        _jobs[job_id] = result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/submit", methods=["POST"])
def submit():
    """Accept patient notes and kick off the autonomous crew pipeline."""
    data = request.get_json(silent=True) or {}
    patient_data = (data.get("patient_data") or "").strip()
    patient_id = (data.get("patient_id") or "PATIENT").strip()

    if not patient_data:
        return jsonify({"error": "patient_data is required"}), 400

    if len(patient_data) < 50:
        return jsonify({"error": "Patient notes are too short. Please provide full clinical notes."}), 400

    # Use a simple job ID
    import uuid
    job_id = str(uuid.uuid4())

    with _jobs_lock:
        _jobs[job_id] = {"status": "running"}

    thread = threading.Thread(
        target=_run_crew_async,
        args=(job_id, patient_data, patient_id),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id, "status": "running"})


@app.route("/api/status/<job_id>")
def status(job_id: str):
    """Poll the status of a running crew job."""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if "status" in job and job["status"] == "running":
        return jsonify({"status": "running"})

    # Job is done — return full result
    return jsonify({"status": "complete", "result": job})


@app.route("/api/jobs")
def list_jobs():
    """Return a list of all completed job IDs and their run info."""
    with _jobs_lock:
        summary = [
            {
                "job_id": jid,
                "run_id": data.get("run_id", ""),
                "success": data.get("success", False),
                "qa_score": data.get("qa_score", 0),
                "files": data.get("files", []),
            }
            for jid, data in _jobs.items()
            if isinstance(data, dict) and "run_id" in data
        ]
    return jsonify(summary)


@app.route("/output/<path:filename>")
def serve_output(filename: str):
    """Serve files from the output directory."""
    output_dir = Path("output").resolve()
    return send_from_directory(output_dir, filename)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "MedScribe AI"})


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    app.run(debug=is_debug(), host="0.0.0.0", port=5000)
