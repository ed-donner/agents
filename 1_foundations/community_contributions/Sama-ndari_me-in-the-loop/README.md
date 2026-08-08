# Personal AI Clone (Week 1)

Digital twin chatbot with document context + OpenAI tool calling + Gradio + Pushover.

Week 1 patterns: load local files into a system prompt, function tools, Gradio chat UI.

## What it does

- Answers from files you place in `me/` (PDF, DOCX) and optional URLs in `me/links.txt`
- Tools: `record_user_details`, `record_unknown_question` (Pushover when configured)
- Gradio UI (`app.py`) and walkthrough notebook (`personal_ai_clone.ipynb`)

## Knowledge files (not in this PR)

Large resume/brain binaries are kept out of the course repo (Ed’s size guidance).

Add your own docs under `me/`, or download sample files from the full project:

https://github.com/Sama-ndari/personal-ai-clone

Expected layout:

```
me/
  resume.pdf          # optional — your CV
  AI-CLONE-BRAIN.docx # optional — Q&A / biography
  links.txt           # optional — URLs to scrape
  summary.md          # tiny demo context (included)
```

## Setup

Use the course `uv` environment from the repo root (preferred). Then:

```bash
cd 1_foundations/community_contributions/Sama-ndari_me-in-the-loop
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=your_key
PUSHOVER_USER=optional
PUSHOVER_TOKEN=optional
```

## Run

```bash
python app.py
```

Or open `personal_ai_clone.ipynb` and run the cells.

Full project: https://github.com/Sama-ndari/personal-ai-clone

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
