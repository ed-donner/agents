---
title: deep_research
app_file: app.py
sdk: gradio
sdk_version: 5.49.1
---
# Deep Research — Capstone Project (2_openai)

Production-style **Deep Research** agent: input guardrails → clarifying questions → autonomous manager (plan → search → write → evaluate → optimize) → optional email. Uses **citation layer** ([1], [2] + Sources section) and **OpenAI SDK** (guardrails + openai-agents). See **CAPSTONE.md** for how every 2_openai lab idea maps into this project.

**Features:** Input guardrails (intent, PII, length) · Clarifying questions (3) · Agentic manager (agents as tools + handoff) · Evaluator–optimizer · Citation layer · Recipient email · Streaming UI · Gradio share + Hugging Face Space.

## Run locally

```bash
cd 2_openai/deep_research
pip install -r requirements.txt
# Set OPENAI_API_KEY (and SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, DEFAULT_RECIPIENT_EMAIL if using email)
python deep_research.py
```

- **share=True** is set in `deep_research.py`: you get a public **gradio.live** link so others can open the app.

---

## Deploy as a Hugging Face Space

### 1. Create the Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces).
2. Click **Create new Space**.
3. Choose **Gradio** as SDK, pick a name (e.g. `deep-research`), set visibility (Public/Private), then **Create Space**.

### 2. Add your files

From your repo, the Space needs the contents of `2_openai/deep_research/`:

- `app.py` (entry point)
- `deep_research.py`
- `research_manager.py`
- `clarifier_agent.py`
- `evaluator_agent.py`
- `manager_agent.py`
- `planner_agent.py`
- `search_agent.py`
- `writer_agent.py`
- `email_agent.py`
- `guardrails.py`
- `requirements.txt`
- `.env.example` (optional; copy to `.env`)

You can:

- **Push with Git**: clone the Space repo, copy these files into it, commit and push.
- Or **upload** the same files in the Space’s “Files” tab.

### 3. Set secrets

In the Space: **Settings → Repository secrets** (or **Variables and secrets**):

- `OPENAI_API_KEY` (required)
- Optional: `SENDGRID_API_KEY`, `SENDGRID_FROM_EMAIL`, `DEFAULT_RECIPIENT_EMAIL` if you want email.

### 4. Run the Space

The Space runs:

```bash
gradio run app.py
```

(or the equivalent that Hugging Face uses for Gradio). The app will be live at:

`https://huggingface.co/spaces/<your-username>/<space-name>`.

---

## Quick share (local only)

Run:

```bash
python deep_research.py
```

You’ll get a local URL and a **gradio.live** link; the latter is public for 72 hours so others can open the app without deploying to Hugging Face.
