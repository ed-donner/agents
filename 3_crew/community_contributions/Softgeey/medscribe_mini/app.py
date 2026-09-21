"""
MedScribe Mini — Autonomous Discharge Summary Generator
Single-file Flask app. 3-agent pipeline powered by OpenRouter.
"""

import json, os, re, threading, uuid
import requests
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "medscribe-mini-secret")

_jobs: dict = {}
_lock = threading.Lock()

# ── Config ────────────────────────────────────────────────────────────────────

MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key or "your_key" in key:
        raise ValueError("Set OPENROUTER_API_KEY in your .env file.")
    return key


# ── LLM call ─────────────────────────────────────────────────────────────────

def llm(system: str, user: str, temp: float = 0.3) -> str:
    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {get_key()}",
                 "Content-Type": "application/json"},
        json={"model": MODEL, "temperature": temp,
              "messages": [{"role": "system", "content": system},
                           {"role": "user",   "content": user}]},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


# ── Agents ────────────────────────────────────────────────────────────────────

def agent_analyst(notes: str) -> str:
    """Extract structured clinical facts from raw patient notes."""
    return llm(
        "You are a clinical data analyst. Extract all medically relevant facts "
        "from the patient notes into clean, structured JSON. Output ONLY valid JSON.",
        f"Extract structured data:\n\n{notes}",
        temp=0.1,
    )


def agent_writer(clinical_json: str) -> str:
    """Write a professional discharge summary from structured data."""
    return llm(
        "You are a board-certified medical writer. Write a complete, professional "
        "discharge summary using the structured patient data provided. "
        "Use clear section headers. Plain text only.",
        f"Write the discharge summary from:\n\n{clinical_json}",
        temp=0.4,
    )


def agent_qa(summary: str) -> dict:
    """QA review — score the summary and flag any issues."""
    raw = llm(
        "You are a Chief Medical Officer auditing clinical documentation. "
        "Review the discharge summary for completeness and safety. "
        "Output ONLY valid JSON: {\"score\": 0-100, \"approved\": true/false, \"issues\": []}",
        f"Review:\n\n{summary}",
        temp=0.1,
    )
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group()) if m else {"score": 0, "approved": False, "issues": ["Parse error"]}


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(job_id: str, notes: str) -> None:
    try:
        clinical  = agent_analyst(notes)
        summary   = agent_writer(clinical)
        qa        = agent_qa(summary)
        with _lock:
            _jobs[job_id] = {
                "success":  True,
                "summary":  summary,
                "qa_score": qa.get("score", 0),
                "approved": qa.get("approved", False),
                "issues":   qa.get("issues", []),
            }
    except Exception as exc:
        with _lock:
            _jobs[job_id] = {"success": False, "error": str(exc)}


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def run():
    data  = request.get_json(silent=True) or {}
    notes = (data.get("notes") or "").strip()
    if len(notes) < 50:
        return jsonify({"error": "Patient notes too short."}), 400
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {"status": "running"}
    threading.Thread(target=run_pipeline, args=(job_id, notes), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Not found"}), 404
    if "status" in job:
        return jsonify({"status": "running"})
    return jsonify({"status": "done", "result": job})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("MedScribe Mini → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG", "false") == "true")
