# Personal AI Assistant – AMA Chatbot

## Why this project?

A portfolio chatbot that acts as **you** — answering questions about your career, background and skills as if you were there. It also captures leads (email + notes) when visitors want to get in touch, and can generate a polished HTML résumé on demand.

---

## What makes it technically interesting?

### Multi-model agentic pipeline
The résumé generation is handled by a **three-stage agent loop** where each stage is powered by a different LLM provider:

| Stage | Model | Role |
|-------|-------|------|
| **Extractor** | OpenAI (`gpt-5-mini`) | Parses your LinkedIn PDF into structured JSON |
| **Planner** | Anthropic Claude (`claude-sonnet-4-6`) | Writes a design brief for the résumé |
| **Developer** | Google Gemini (`gemini-3.1-flash-lite-preview`) | Renders the full single-file HTML résumé |

Each agent uses **tool calling** (create / complete todos) to plan its work before executing, making the reasoning process visible in the UI.

### Streaming UI
The Gradio interface **streams intermediate steps** in real time — you see the agent logs updating as each tool is called, rather than waiting for a final response.

### Provider-agnostic agent runner
A single `run_agent_stream()` dispatcher routes to OpenAI, Anthropic, or Gemini based on the model name, with each backend translating the shared OpenAI-style tool schema into the provider's native format.

---

## How to use it

### 1. Prerequisites

```bash
uv pip install -r requirements.txt
```

### 2. Environment variables

Create a `.env` file at the project root (or export the variables):

```env
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...

# Optional – Pushover notifications for leads
PUSHOVER_TOKEN=...
PUSHOVER_USER=...
```

### 3. Personal data

Place your files in a `me/` folder next to `app.py`:

```
me/
  linkedin.pdf   ← export from LinkedIn
  me.txt         ← a short free-text bio / summary
```

### 4. Run

```bash
uv run app.py
```

Then open the Gradio URL printed in the terminal (default: `http://localhost:7861`).

### 5. Chat commands

| What you say | What happens |
|---|---|
| Anything about career / skills | Bot answers using your LinkedIn + bio |
| Provide your email | Email & context are recorded via Pushover |
| *"Show me your resume"* | Triggers the 3-stage agent pipeline; HTML résumé appears below the chat |
