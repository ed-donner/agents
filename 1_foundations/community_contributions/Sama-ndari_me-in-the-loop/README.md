# Personal AI Clone (Week 1)

Digital twin chatbot with RAG + OpenAI tool calling + Gradio + Pushover notifications.

Built for the Agentic AI Engineering Course (Week 1 foundations): resume/PDF context, function tools, and a chat UI.

## What it does

- Answers questions from files in `me/` (PDF, DOCX) and optional URLs in `me/links.txt`
- Tools: `record_user_details`, `record_unknown_question` (Pushover when configured)
- Gradio chat UI (`app.py`) and walkthrough notebook (`personal_ai_clone.ipynb`)

## Setup

```bash
cd 1_foundations/community_contributions/Sama-ndari_me-in-the-loop
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` (do not commit it):

```
OPENAI_API_KEY=your_key
PUSHOVER_USER=optional
PUSHOVER_TOKEN=optional
```

Replace `me/resume.pdf` (and optional DOCX / links) with your own data if you want.

## Run

```bash
python app.py
```

Or open `personal_ai_clone.ipynb` and run the cells.

Full project (optional): https://github.com/Sama-ndari/personal-ai-clone

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
