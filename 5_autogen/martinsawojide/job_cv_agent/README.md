# Agentic Job Application System

An automated, multi-agent pipeline that reads a job URL and a candidate CV, then produces a tailored resume, structured application answers, and an alignment report — all without human intervention in the loop.

---

## What it does

You give the system two things: a job posting URL and a CV (PDF). It runs the full pipeline below and outputs three files:

- **`resume.pdf`** — a tailored resume compiled from Typst source, keyword-matched to the job description
- **`application_answers.txt`** — honest, evidence-grounded answers to every application form question
- **`report.md`** — a structured alignment report with an overall hire verdict, per-committee breakdown, strengths, gaps, objections, mitigations, and interview talking points

---

## Pipeline

```
Job URL + CV PDF
       │
       ▼
   ScoutAgent          — scrapes job page, extracts JD text and form questions (LangChain Playwright)
       │
       ▼
 ResearcherAgent       — researches company via Serper (web + news), produces a cited company profile
       │                 with a 10x impact assessment
       ▼
 generate_personas()   — generates 10 named hiring committee identities tailored to the specific JD
       │
       ▼
 5 × CommitteeModerator (parallel asyncio.gather)
   ├── Technical Skills
   ├── Experience
   ├── Cultural Fit
   ├── Career Trajectory
   └── Impact & Leadership
       │
       ▼
    Aggregator          — synthesises all verdicts, generates 3 outputs in parallel,
                          runs CVCritic revision loop (up to 2 passes), compiles PDF via Typst CLI
```

---

## Agents

### ScoutAgent
- Initialises a headless Chromium browser via LangChain's `PlayWrightBrowserToolkit`
- Uses an `AssistantAgent` delegate (GPT-4o-mini) to navigate to the job URL
- Extracts the raw job description, detects the apply link, and scrapes any application form questions
- Returns a `JobBrief` with all scraped data

### ResearcherAgent
- Runs Serper web and news search on the company name extracted from the JD
- Produces a concise company profile (max 400 words) covering: products, engineering culture, recent news (funding, layoffs, pivots), tech stack, team structure, and red flags
- Cites up to 5 sources inline
- Closes with a one-sentence 10x assessment: is this a credible vehicle for order-of-magnitude impact?

### generate_personas (function)
- Calls GPT-4o-mini to refine 10 fixed named role identities into 2-3 sentence system messages tailored to the specific job and company
- Each committee gets an Advocate persona (argues for the candidate) and a Skeptic persona (argues against)
- Falls back to built-in named identities if the LLM call fails

### CommitteeModerator (×5, run in parallel)
Each moderator runs a structured debate for its dimension:

1. **Advocate opens** — argues FOR the candidate using only CV evidence; ends every argument with `SCORE: X/10 | KEY EVIDENCE: ...`
2. **Skeptic rebuts** — surfaces genuine CV-to-JD gaps; ends every argument with `SCORE: X/10 | KEY GAP: ...`
3. **Advocate defends** — defends against the rebuttal with new CV evidence
4. **Extended rounds** — up to 3 additional turns, each fired with 40% probability (`REPLY_PROBABILITY = 0.4`), giving a hard maximum of 6 turns

After the debate, a synthesis delegate (Claude Sonnet) produces a structured `CommitteeVerdict` containing:
- `hire_label` — one of: Strong Hire / Lean Hire / No Hire / Hold
- `score` — 0–10 for this dimension
- `confidence_pct` — the model's confidence in the score (0–100%)
- `pros` / `cons` — 2-3 evidence bullets each
- `top_objection` — the single hardest objection a hiring manager would raise
- `mitigation` — a concrete tactical mitigation (probation goal, test task, or reference question)
- `cv_gaps` — list of JD requirements not evidenced in the CV

#### Committee Dimensions

| Committee | Advocate Role | Skeptic Role |
|---|---|---|
| Technical Skills | Technical Lead | Senior Engineer |
| Experience | Hiring Manager | Department Head |
| Cultural Fit | People & Leadership Coach | Culture Skeptic |
| Career Trajectory | Product & Strategy Lead | Growth Skeptic |
| Impact & Leadership | External Industry Expert | Executive Skeptic |

### Aggregator
Receives the `JobBrief` and all 5 `CommitteeVerdict` objects. Runs three outputs in parallel:

1. **Typst resume writer** (Claude Sonnet) — tailors the CV template to the JD; keywords are reframed, sections reordered, achievements strengthened. Fabrication is explicitly prohibited.
2. **QA writer** (Claude Sonnet) — answers each application form question honestly; leads with strongest relevant experience, quantifies outcomes, mirrors JD vocabulary.
3. **Report writer** (Claude Sonnet) — produces a structured Markdown report with overall hire verdict, committee score table, strengths, gaps with mitigations, and interview talking points.

Then runs the **CVCritic loop** (up to 2 passes):

- **CVCritic** (Claude Sonnet) evaluates the Typst draft on three axes:
  - `alignment_score` (0–10): JD keyword and requirement match
  - `fidelity_score` (0–10): faithfulness to the original CV — fabrication directly reduces this score
  - `positioning_score` (0–10): strength of narrative positioning for the specific role
- If either `alignment_score < 7` or `fidelity_score < 8`, the critic issues revision instructions in three sections: Language Improvements, Fabrication Reversions, Positioning Upgrades
- The Typst writer applies the revisions and the cycle repeats
- A warning is appended to the report if max loops are hit without convergence

### Typst Compiler
- Calls the local `typst compile` CLI via `asyncio.create_subprocess_exec`
- On compilation failure, the error is sent back to the Typst writer for an LLM-driven fix, then retried (up to 3 attempts)

---

## Outputs

| File | Format | Description |
|---|---|---|
| `outputs/resume.typ` | Typst source | Tailored resume source code |
| `outputs/resume.pdf` | PDF | Compiled resume (requires Typst CLI) |
| `outputs/application_answers.txt` | Plain text | Q&A pairs, one per question |
| `outputs/report.md` | Markdown | Full alignment report with hire verdict |

---

## Tools and Techniques

| Tool / Technique | Where used | Purpose |
|---|---|---|
| **AutoGen `AssistantAgent`** | All agents | LLM interaction with structured output support |
| **Pydantic `BaseModel`** | `messages.py` | All data contracts between components — no TypedDicts or dataclasses |
| **`asyncio.gather`** | `main.py` | Parallel execution of 5 committee moderators |
| **LangChain `PlayWrightBrowserToolkit`** | `tools.py` / `scout.py` | Agentic browser-based job page scraping |
| **LangChain `GoogleSerperAPIWrapper`** | `tools.py` | Web + news search for company research |
| **`autogen_ext` `LangChainToolAdapter`** | `tools.py` | Bridges LangChain tools into AutoGen's tool interface |
| **Typst CLI** | `main.py` | PDF compilation of the tailored resume |
| **`pdfplumber`** | `tools.py` | PDF text extraction from candidate CV |
| **Gradio 6** | `ui.py` | Web UI for inputs, real-time status, and file downloads |
| **Python `logging`** | `ui.py` | Custom handler routes `[STAGE]`-prefixed log lines to the UI stage display |
| **Named role identities** | `committee.py` | Each advocate/skeptic has a defined professional role (not just "advocate"), improving debate quality |
| **Structured debate format** | `committee.py` | Every argument ends with `SCORE: X/10 | KEY EVIDENCE/GAP: ...` for traceable reasoning |
| **Self-healing Typst loop** | `main.py` | Compilation errors are fed back to the LLM for automated correction |
| **CVCritic three-axis evaluation** | `aggregator.py` | Alignment + fidelity + positioning — prevents both hallucination and weak positioning |
| **Fallback verdicts** | `committee.py` | Failed debate rounds produce a zero-score verdict so the pipeline never stalls |

---

## Models

| Role | Model | Provider |
|---|---|---|
| Scout, Researcher, Persona generation | `openai/gpt-4o-mini` | OpenAI via OpenRouter |
| Advocate (all committees) | `anthropic/claude-haiku-4.5` | Anthropic via OpenRouter |
| Skeptic (all committees) | `x-ai/grok-3-mini` | xAI via OpenRouter |
| Synthesis, Aggregator, CVCritic | `anthropic/claude-sonnet-4.5` | Anthropic via OpenRouter |

---

## Setup

### Prerequisites
- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) package manager
- [Typst CLI](https://typst.app/docs/tutorial/): `cargo install typst-cli` or platform binary
- Playwright browsers: `playwright install chromium`

### Environment variables (`.env`)
```
OPENROUTER_API_KEY=...
SERPER_API_KEY=...
```

### Run

```bash
uv run python main.py          # CLI mode (set job_url and cv_path in main.py)
uv run python ui.py            # Gradio web UI (http://localhost:7860)
```

### Inputs folder
On first run, `main.py` creates `inputs/` and `sandbox/` directories next to itself. Place your CV PDF in `inputs/`.

---

## File Structure

```
job_cv_agent/
├── main.py          — pipeline entry point, Typst compilation, file writes
├── ui.py            — Gradio 6 web interface
├── messages.py      — Pydantic data contracts (JobBrief, CommitteeVerdict, FinalOutput, ...)
├── models.py        — OpenAIChatCompletionClient factories for each model
├── tools.py         — Serper search tools, PDF parser, LangChain Playwright browser tools
├── scout.py         — ScoutAgent (scraping) + ResearcherAgent (company research)
├── committee.py     — generate_personas() + AdvocateAgent + SkepticAgent + CommitteeModerator
├── aggregator.py    — Aggregator (output synthesis + CVCritic loop)
├── inputs/          — place CV PDFs and optional Typst templates here
├── outputs/         — generated files written here
└── README.md
```
