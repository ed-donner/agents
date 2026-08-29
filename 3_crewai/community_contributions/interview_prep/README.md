---
title: interview-prep-crew
app_file: app.py
sdk: gradio
sdk_version: 6.20.0
---
# Interview Prep Crew

A multi-agent CrewAI project that researches any company and role to generate a structured, actionable interview preparation guide — then lets you practice with an interactive Gemini-powered mock interview.

## What It Does

Given a company name, role, and optional job description, four specialized agents collaborate to produce:

| Output | File |
|--------|------|
| Structured prep guide (JSON + markdown) | `output/prep_guide.json` / `output/prep_guide.md` |
| Curated real resource links | `output/resources.md` |
| Live mock interview session | terminal (interactive) |

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| Company Researcher | Profiles the company — tech stack, culture, recent news | Serper, Scrape |
| Interview Intel Agent | Finds real past questions from Glassdoor, LeetCode, Reddit, Blind | Serper, Scrape |
| Resource Curator | Finds real working prep links (only URLs from search results) | Serper |
| Interview Strategist | Synthesizes everything into a structured JSON prep guide | None (reasoning only) |

## Structured Output (Pydantic)

The prep guide is returned as a validated Pydantic model and saved as JSON:

```json
{
  "company": "Google",
  "role": "Software Engineer",
  "round_breakdown": ["..."],
  "topic_weightage": [
    { "topic": "DSA", "weightage_percent": 40, "sample_questions": ["..."] }
  ],
  "one_week_plan": "Day 1: ...",
  "must_know_questions": ["..."]
}
```

## Mock Interview

After the crew runs, you can start an interactive mock interview powered by Gemini. The interviewer has full context from the prep guide — it asks one question at a time, gives feedback after each answer, and covers DSA, System Design, and Behavioral rounds. Type `quit` to end and get overall feedback.

## Setup

**Requirements:** Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
cd interview_prep
crewai install
```

Add your keys to a `.env` file:

```env
GEMINI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here   # free at serper.dev (2500 searches/month)
```

## Running

```bash
uv run crewai run
```

You will be prompted for:
1. Company name
2. Role
3. Job description (optional — paste it in, press Enter twice to skip)

After the crew finishes, you'll be asked if you want to start a mock interview session.

## LLM

Uses `gemini/gemini-3.1-flash-lite` via LiteLLM. Change the `llm:` field in `config/agents.yaml` to use any other model supported by CrewAI (OpenAI, Anthropic, etc.).

## Project Structure

```
interview_prep/
├── src/interview_prep/
│   ├── crew.py              # Agent + task wiring, Pydantic models
│   ├── main.py              # Entry point, mock interview session
│   └── config/
│       ├── agents.yaml      # Agent definitions
│       └── tasks.yaml       # Task definitions
├── pyproject.toml
└── README.md
```

## Author

Shivam Garg — built as part of Ed Donner's Agentic AI course (Week 3 — CrewAI).
