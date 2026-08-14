# Twin Agent

An AI-powered **digital twin** that represents a real person on their personal website. Visitors (recruiters, potential clients, collaborators) chat with the twin to learn about the person's career, background, skills, and experience. The twin answers from the owner's LinkedIn profile, a short summary, and a searchable **vector knowledge base**, stays in character, and can capture leads by pushing notifications when someone wants to get in touch.

## Table of Contents
- [Overview](#overview)
- [How It Works](#how-it-works)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Knowledge Base Setup](#knowledge-base-setup)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [Deployment](#deployment)
- [Customizing the Twin](#customizing-the-twin)
- [References](#references)

## Overview

Twin Agent is a conversational AI web app that acts as a digital representative of a professional. It is grounded in three sources of truth about the person it represents:

1. A LinkedIn profile exported as a PDF (`info/profile.pdf`)
2. A short text summary (`info/summary.txt`)
3. A **vector knowledge base** (`info/knowledge.csv`) — stored in PostgreSQL with semantic search powered by Hugging Face embeddings

The twin never invents answers outside that context, always discloses that it is an AI digital twin, and routes interested visitors to a lead-capture tool that sends a push notification to the owner.

## How It Works

```
Visitor message
      │
      ▼
 Gradio chat loop  ────────────────────────────────────────────────────
      │
      ▼
 Digital Twin agent (Groq · gpt-oss-120b)
   ├─ calls tools?  ─── yes ──► ┌─────────────────────────────────────┐
      │                        │  • record_user_details              │
      │                        │  • record_unknown_question        │
      │                        │  • query_knowledge (vector search)  │
      │                        │                                     │
      │                        └────────────┬────────────────────────┘
      │                                     │
      │                                     ▼
      │                        Pushover notification to owner
      │                                     │
      │                        KnowledgeStore (PostgreSQL + pgvector)
      │                                     │
      │                        Hugging Face Inference API
      │                        (multilingual-e5-large-instruct)
      │
      └─ no tools ──► UserMessageValidator (Groq)
                        │
                        └─ recruiter-style question?
                              yes ──► TwinResponseReviewer (Azure Foundry · gpt-5-nano)
                                        │
                                        ├─ is_ok: true  ──► return response
                                        └─ is_ok: false ──► feed suggestions back, re-prompt
```

The twin is grounded by a system prompt built at startup from the PDF profile and text summary. When a visitor asks about topics beyond the LinkedIn profile, the twin uses the **`query_knowledge` tool** to perform a semantic search over the vector knowledge base. Two auxiliary agents guard quality:

- **User Message Validator** — Decides whether a message is recruiter-relevant before spending tokens on a full review.
- **Twin Response Reviewer** — Scores the twin's reply against persona rules (discloses it is a twin, shows interest, states knowledge limits) and returns `{ "is_ok": bool, "suggestions": "..." }`. If `is_ok` is false, the suggestions are fed back to the twin for a corrected response.

## Features

- Persona-grounded chat strictly limited to the owner's profile, summary, and knowledge base
- **Semantic knowledge retrieval** — vector search over a curated Q&A knowledge base powered by PostgreSQL + pgvector + Hugging Face embeddings
- Automatic disclosure that the twin is an AI representative
- Lead capture: records visitor email/name/notes and pushes a Pushover notification
- Unanswered-question logging for follow-up insight
- Dual-agent quality review pipeline (validator + response reviewer)
- Multi-provider credentials via the OpenAI SDK (Groq, OpenRouter, Azure Foundry)
- Custom Gradio dark/light theme with blue/red accent palette and gradient title
- Example prompts and auto-focus input for a polished UX
- Containerized with Docker; CI builds to GHCR and deploys to Render

## Tech Stack

| Layer            | Technology                                                               |
|------------------|--------------------------------------------------------------------------|
| Language         | Python 3.12                                                              |
| Web UI           | Gradio                                                                   |
| LLM access       | OpenAI SDK (OpenAI-compatible endpoints)                                 |
| Providers        | Groq (`gpt-oss-120b`), Azure Foundry (`gpt-5-nano`), OpenRouter          |
| Profile input    | PyPDF (reads `info/profile.pdf`)                                         |
| Knowledge base   | PostgreSQL 14+ with `pgvector` extension                                 |
| Embeddings       | Hugging Face Inference API (`intfloat/multilingual-e5-large-instruct`)   |
| Knowledge ingest | `pandas` (reads `info/knowledge.csv`)                                    |
| Notifications    | Requests + Pushover API                                                  |
| Config           | python-dotenv                                                            |
| Packaging        | `uv` (lockfile: `src/uv.lock`), `pyproject.toml` + `requirements.txt`    |
| Container        | Docker (python:3.12-slim)                                              |
| CI/CD            | GitHub Actions -> GHCR -> Render deploy hook                             |

## Project Structure

```
twin_agent/
├── .github/
│   └── workflows/
│       └── dev.yml            # Build/push to GHCR + Render deploy
├── info/
│   ├── knowledge.csv          # Q&A knowledge base (grounding source #3)
│   ├── profile.pdf            # LinkedIn export (grounding source #1)
│   └── summary.txt            # Short bio (grounding source #2)
├── src/
│   ├── agentic/
│   │   ├── agents.py          # TwinResponseReviewer, UserMessageValidator
│   │   └── context.py         # Reviewer/validator system prompts
│   ├── context.py             # Builds system prompt from profile + summary
│   ├── data/
│   │   ├── db.py              # KnowledgeStore: embeddings + vector search
│   │   └── seed.py            # Ingests knowledge.csv into PostgreSQL
│   ├── digital_twin.py        # Core persona agent (Groq)
│   ├── main.py                # Gradio app + chat orchestration loop
│   ├── notifications.py       # Pushover notification client
│   ├── providers.py           # Multi-provider credential router
│   ├── requirements.txt
│   ├── styles.py              # Gradio theme CSS, JS, example prompts
│   └── tools.py               # Function tools (lead capture, question log, knowledge search)
├── .env.example
├── .gitignore
├── Dockerfile
└── README.md
```

## Prerequisites

- Python >= 3.12
- **PostgreSQL 14+** with the `pgvector` extension installed
- A Groq account with an API key (primary twin + message validator)
- An Azure Foundry endpoint and key for the response reviewer model (`gpt-5-nano`)
- A Hugging Face account with an API token for embeddings
- A Pushover account (user + token) to receive lead and unanswered-question notifications
- (Optional) An OpenRouter API key if you want to use that provider
- Docker (for containerized runs)

### PostgreSQL + pgvector Setup

If you do not have a running PostgreSQL instance with `pgvector`, the quickest way is to use Docker:

```bash
docker run -d \
  --name twin-postgres \
  -e POSTGRES_USER=twin \
  -e POSTGRES_PASSWORD=twin \
  -e POSTGRES_DB=twin_kb \
  -p 5432:5432 \
  ankane/pgvector:latest
```

Then set `POSTGRESS_CONN_STRING` (or individual `POSTGRES_*` variables) in your `.env` file.

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/<owner>/twin_agent.git
   cd twin_agent
   ```

2. Copy the environment template and fill in your secrets:

   ```bash
   cp .env.example .env
   ```

   Then edit `.env` with your provider keys, Pushover credentials, PostgreSQL connection details, and Hugging Face token.

3. Install dependencies (from the `src/` directory). This is a **uv** project — `uv sync` is preferred and reads the locked dependencies from `uv.lock`; `pip` works as a fallback:

   ```bash
   cd src
   uv sync            # preferred (uses uv.lock)
   # — or —
   pip install -r requirements.txt
   ```

   > **Dependency note:** `requirements.txt` and `pyproject.toml` declare `dotenv>=0.9.9`, but the code imports `from dotenv import load_dotenv`, which is the API of the **`python-dotenv`** package (a different distribution). `uv.lock` already resolves this correctly; if you re-pin deps by hand, use `python-dotenv`, not `dotenv`.

4. **Seed the knowledge base** (one-time setup):

   ```bash
   cd src/data
   python seed.py
   ```

   This reads `info/knowledge.csv`, generates embeddings via Hugging Face, and stores the chunks in the `documents` table with a pgvector `ivfflat` index.

## Environment Variables

All variables are defined in `.env.example`:

| Variable                  | Description                                               | Required for            |
|---------------------------|-----------------------------------------------------------|-------------------------|
| `GROQ_ENDPOINT`           | Groq OpenAI-compatible endpoint                           | Twin + validator        |
| `GROQ_API_KEY`            | Groq API key                                              | Twin + validator        |
| `AZURE_FOUNDRY_ENDPOINT`  | Azure Foundry endpoint                                    | Response reviewer       |
| `AZURE_FOUNDRY_API_KEY`   | Azure Foundry API key                                     | Response reviewer       |
| `OPENROUTER_ENDPOINT`     | OpenRouter endpoint (optional alternative)                | Optional                |
| `OPENROUTER_API_KEY`      | OpenRouter API key (optional alternative)                 | Optional                |
| `PUSHOVER_USER`           | Pushover user key                                         | Lead notifications      |
| `PUSHOVER_TOKEN`          | Pushover app token                                        | Lead notifications      |
| `POSTGRESS_CONN_STRING`   | PostgreSQL connection string (e.g. `postgresql://...`)    | Knowledge base          |
| `POSTGRES_HOST`           | PostgreSQL host                                           | Knowledge base (alt)    |
| `POSTGRES_PORT`           | PostgreSQL port                                           | Knowledge base (alt)    |
| `POSTGRES_USER`           | PostgreSQL user                                           | Knowledge base (alt)    |
| `POSTGRES_PASSWORD`       | PostgreSQL password                                       | Knowledge base (alt)    |
| `POSTGRES_DB`             | PostgreSQL database name                                  | Knowledge base (alt)    |
| `HF_TOKEN`                | Hugging Face API token for embeddings                     | Knowledge base          |
| `OPENCOODE_API_KEY`       | *(vestigial — present in `.env.example` but not referenced by any code; safe to leave blank)* | None |

> The Pushover user key should start with `u` and the token with `a`; the app logs a validation hint on startup.

## Knowledge Base Setup

The knowledge base extends the twin's answers beyond the LinkedIn profile. It is stored as a CSV and ingested into a vector database.

### File format: `info/knowledge.csv`

The CSV has two columns:

| Column     | Description                                          |
|------------|------------------------------------------------------|
| `question` | A recruiter-style question this row answers          |
| `answer`   | The answer text. Multiple variants per row can be separated with `\|\|` |

**Example:**

```csv
question,answer
"What is your approach to system design?","I start with requirements gathering and constraints||I draw architecture diagrams before writing code||I prefer iterative design over big-up-front"
"Tell me about a challenging project","Led a migration from monolith to microservices||Reduced deployment time by 80%"
```

### Seeding

Run the seed script whenever you update `knowledge.csv`:

```bash
cd src/data
python seed.py
```

What the script does:
1. Initializes the `documents` table with a `vector(1024)` column (matching the `multilingual-e5-large-instruct` output dimension).
2. Creates an `ivfflat` index for fast cosine-similarity search.
3. Reads each row from `knowledge.csv`, splits answers on `\|\|`, embeds the chunks via Hugging Face, and inserts them with JSONB metadata (`{"question": "..."}`).

### How the twin uses it

When a visitor asks something not obviously in the LinkedIn profile, the twin may call the `query_knowledge` tool. The tool:
1. Embeds the visitor's question using the same Hugging Face model.
2. Runs a cosine-similarity `ORDER BY` against the `documents` table.
3. Returns the top-5 most similar chunks with relevance scores.
4. The twin incorporates those chunks into its response, staying grounded in the owner's actual knowledge.

## Running Locally

The app runs from the `src/` directory — its top-level imports (`import context`, `from digital_twin import DigitalTwin`, `from providers import AiProvider`) only resolve when `src/` is on `sys.path`.

From the `src/` directory:

```bash
uv run python main.py     # preferred (uses the project venv)
# — or —
python main.py            # inside an activated src/.venv
```

The Gradio web UI launches at `http://localhost:7860` with the title **Digital Twin** and the description *"Talk to my AI twin about my career"*.

## Running with Docker

Build and run the image (matching the Render deployment configuration):

```bash
docker build -t twin-agent .
docker run --env-file .env -p 7860:7860 twin-agent
```

The container binds `0.0.0.0:7860` (via `GRADIO_SERVER_NAME=0.0.0.0` in the Dockerfile) so the port can be discovered by Render's dynamic `$PORT`.

## Deployment

Deployment is automated through `.github/workflows/dev.yml`:

1. On push to `main`, GitHub Actions builds the Docker image and pushes it to GHCR (`ghcr.io/<owner>/digital-twin:latest` and a commit-SHA tag).
2. The workflow syncs environment variables to the Render service via the Render API.
3. A deploy hook is triggered to pull the new image and restart the Render web service.

Required GitHub repository secrets for the workflow:

- `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_DEPLOY_HOOK`
- The same provider/Pushover/PostgreSQL/Hugging Face variables listed in [Environment Variables](#environment-variables)

## Customizing the Twin

The twin's persona is driven by the contents of the `info/` directory. No code changes are required to make it represent a different person:

- **Replace** `info/profile.pdf` with that person's LinkedIn export PDF.
- **Edit** `info/summary.txt` to describe the person in a few lines.
- **Edit or replace** `info/knowledge.csv` with their curated Q&A pairs.
- **Re-seed** the knowledge base after any CSV change: `cd src/data && python seed.py`.

The system prompt in `src/context.py` (`get_system_prompt`) is automatically rebuilt from the PDF and summary on startup. The `query_knowledge` tool is registered in `src/tools.py` and injected into the twin via `src/main.py`.

To change the visual identity, edit the palette constants (`BLUE`, `RED`) and the CSS variables in `src/styles.py`. To change the example prompts shown in the UI, edit the `EXAMPLES` list in the same file.

## References

- [Gradio documentation](https://www.gradio.app/docs)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Groq API](https://console.groq.com/docs)
- [Azure AI Foundry](https://learn.microsoft.com/azure/ai-foundry/)
- [PyPDF](https://pypdf.readthedocs.io/)
- [Pushover API](https://pushover.net/api)
- [pgvector](https://github.com/pgvector/pgvector)
- [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index)
- [intfloat/multilingual-e5-large-instruct](https://huggingface.co/intfloat/multilingual-e5-large-instruct)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Render deploy hooks](https://render.com/docs/deploy-hooks)

*Last Updated: 14 Aug 2026*
