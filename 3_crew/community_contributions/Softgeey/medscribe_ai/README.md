# MedScribe AI
### Autonomous Discharge Summary Generator — AI Engineering Team

> An autonomous multi-agent system that transforms raw patient clinical notes into
> complete, QA-reviewed discharge summary packages including structured data,
> discharge plans, professional clinical documents, and deployable Python code.

---

## Business Problem

Hospitals lose **$2,000–$10,000 per readmission** caused by incomplete or delayed
discharge summaries. Physicians spend 30–60 minutes manually writing each summary —
time taken away from patient care. Incomplete summaries cause:

- Preventable readmissions (cost: billions annually)
- Billing delays and claim rejections
- Regulatory non-compliance and audit failures
- Medication errors at care transitions

**MedScribe AI** reduces discharge summary time from ~45 minutes to ~2 minutes,
with a built-in QA review ensuring completeness and clinical accuracy.

---

## The AI Engineering Team (5 Agents)

| # | Agent | Role | Output |
|---|-------|------|--------|
| 1 | **Clinical Analyst** | Extracts structured clinical facts from raw notes | `01_clinical_data.json` |
| 2 | **Discharge Planner** | Builds a safe, comprehensive discharge plan | `02_discharge_plan.json` |
| 3 | **Medical Writer** | Composes the full clinical discharge summary | `03_discharge_summary.txt` |
| 4 | **QA Reviewer** | Audits completeness and safety; scores 0–100 | `04_qa_report.json` |
| 5 | **Code Engineer** | Generates deployable Python EMR integration code | `discharge_generator.py` etc. |

Each agent is a specialist LLM call with a carefully engineered system prompt.
The pipeline is fully autonomous — no human input required between steps.

---

## Tech Stack

- **Agent Framework**: Custom multi-agent orchestration (pure Python)
- **LLM Provider**: OpenRouter (frontier models — Claude, GPT-4o, Gemini, etc.)
- **Web UI**: Flask + vanilla JS (no frontend framework required)
- **Output**: Structured JSON + plain-text clinical documents + Python code files
- **Testing**: Python unittest (32 tests, 100% pass rate)
- **Package Manager**: `uv`

---

## Project Structure

```
medscribe_ai/
├── main.py                        # Application entry point
├── app.py                         # Flask web application & API routes
├── pyproject.toml                 # Project metadata & dependencies
├── .env.example                   # Environment variable template
│
├── src/
│   ├── config.py                  # Config — loads .env, validates secrets
│   ├── crew.py                    # Crew orchestrator — runs all 5 agents in sequence
│   │
│   ├── agents/
│   │   ├── clinical_analyst.py    # Agent 1: Extract structured clinical data
│   │   ├── discharge_planner.py   # Agent 2: Generate discharge plan
│   │   ├── medical_writer.py      # Agent 3: Write discharge summary document
│   │   ├── qa_reviewer.py         # Agent 4: Audit quality and safety
│   │   └── code_engineer.py       # Agent 5: Generate deployable Python code
│   │
│   ├── tasks/
│   │   └── task_runner.py         # Safe task execution wrapper
│   │
│   └── utils/
│       ├── llm_client.py          # Thin OpenRouter API client
│       └── file_writer.py         # Output file management
│
├── templates/
│   └── index.html                 # Single-page web UI
│
├── static/
│   ├── css/style.css              # UI stylesheet
│   └── js/app.js                  # UI logic & API polling
│
├── tests/
│   └── test_medscribe.py          # 32 unit tests (all modules)
│
└── output/                        # Generated run folders (auto-created)
    └── <patient_id>_<timestamp>/
        ├── 01_clinical_data.json
        ├── 02_discharge_plan.json
        ├── 03_discharge_summary.txt
        ├── 04_qa_report.json
        ├── 05_generated_code_raw.txt
        ├── discharge_generator.py
        ├── patient_models.py
        ├── example_usage.py
        └── crew_report.txt
```

---

## Implementation Guide

### Prerequisites

- Python 3.11 or higher
- `uv` package manager
- An OpenRouter API key (https://openrouter.ai/keys)

### Step 1 — Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### Step 2 — Set up the project

```bash
# Unzip and enter the folder
unzip medscribe_ai.zip
cd medscribe_ai

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
uv add flask python-dotenv requests
```

### Step 3 — Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
FLASK_SECRET_KEY=any-long-random-string
FLASK_DEBUG=false
```

**Recommended models on OpenRouter:**
| Model | Cost | Speed | Best for |
|-------|------|-------|---------|
| `anthropic/claude-3.5-sonnet` | ~$3/M tokens | Fast | Best accuracy |
| `openai/gpt-4o` | ~$5/M tokens | Fast | Strong alternative |
| `google/gemini-flash-1.5` | ~$0.35/M tokens | Very fast | Budget option |

### Step 4 — Run tests

```bash
python -m unittest tests.test_medscribe -v
```

All 32 tests should pass. Tests use mocks — no API calls or costs incurred.

### Step 5 — Start the application

```bash
python main.py
```

Open http://localhost:5000 in your browser.

### Step 6 — Generate a discharge summary

1. Click **"Load Sample Patient"** to populate a realistic patient record, or paste your own.
2. Enter a Patient ID/reference.
3. Click **"Generate Discharge Summary"**.
4. Watch the 5-agent pipeline execute in real time.
5. View the discharge summary, output files, and crew execution report.
6. All files are saved to `output/<run_id>/` on the server.

---

## API Reference

The Flask app exposes a REST API for integration with hospital systems:

### POST /api/submit
Submit patient notes for processing.

```bash
curl -X POST http://localhost:5000/api/submit \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PT-20241115",
    "patient_data": "Patient notes here..."
  }'
```

Response:
```json
{ "job_id": "uuid", "status": "running" }
```

### GET /api/status/{job_id}
Poll job status.

```bash
curl http://localhost:5000/api/status/{job_id}
```

Response (running):
```json
{ "status": "running" }
```

Response (complete):
```json
{
  "status": "complete",
  "result": {
    "success": true,
    "run_id": "PT-001_20241115_143022",
    "qa_score": 92,
    "qa_approved": true,
    "discharge_summary": "DISCHARGE SUMMARY\n...",
    "files": ["01_clinical_data.json", ...],
    "tasks": [...]
  }
}
```

### GET /api/jobs
List all completed jobs in the current session.

### GET /health
Health check endpoint.

---

## Production Deployment

### With Gunicorn (recommended)

```bash
uv add gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### With Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv venv && uv add flask python-dotenv requests gunicorn
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### Environment notes for production

- Store `OPENROUTER_API_KEY` in a secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Set `FLASK_DEBUG=false`
- Use a persistent job store (Redis or PostgreSQL) instead of the in-memory `_jobs` dict
- Mount `output/` to persistent storage or an object store (S3, GCS)
- Add authentication middleware before exposing to hospital networks

---

## Extending the System

### Swap the LLM model

Change `OPENROUTER_MODEL` in `.env` — no code changes required.

### Add a new agent

1. Create `src/agents/my_agent.py` with a `run(*args) -> str` function.
2. Import and call it in `src/crew.py` as a new task step.
3. Add tests in `tests/test_medscribe.py`.

### Change output format (e.g. PDF, FHIR)

Post-process `03_discharge_summary.txt` in the crew orchestrator after the
Medical Writer step. Add a formatting utility in `src/utils/`.

---

## Disclaimer

MedScribe AI is a clinical decision support tool. All generated discharge summaries
**must be reviewed and approved by a licensed physician** before being given to patients
or entered into medical records. This system does not replace clinical judgment.

---

*MedScribe AI — Built by an autonomous AI Engineering Team*
