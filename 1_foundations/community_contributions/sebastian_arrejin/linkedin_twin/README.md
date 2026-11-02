# LinkedIn Digital Twin with RAG, SQL FAQ and an Evaluator agent

My solution to the Week 1 Lab 4 exercise: a Gradio site where visitors chat with an AI twin of me about my career,
based on my [LinkedIn profile](https://www.linkedin.com/in/sebastian-arrejin-047981146/).

## What I added

- **RAG knowledge base** (`knowledge_base.py`): the documents in `knowledge/` (Markdown, text or PDF) are split into chunks
  and searched with OpenAI embeddings. If the endpoint can't produce embeddings (for example a local model server),
  it falls back to a TF-IDF keyword search.
- **SQL tools** (`database.py`): a SQLite database with common Q&A that the LLM reads and writes,
  plus unanswered questions and contact requests.
- **Pushover notifications** when a visitor leaves their email or asks something the twin can't answer.
- **Evaluator agent** (`evaluator.py`): every reply is checked with structured outputs for three things:
  every claim is supported by the retrieved evidence (no made-up facts), the tone is formal, and the reply stays on topic.
- **Evaluator-optimizer loop** (`twin.py`): rejected replies are regenerated with the evaluator's feedback (up to 2 retries),
  then replaced by a safe fallback.
- **Guarded writes**: database writes requested by the twin are only committed once the evaluator approves the reply,
  so unverified answers never reach the FAQ.

## How to run

It uses the course's virtual environment and the `.env` in the project root (`OPENAI_API_KEY`, optionally `PUSHOVER_USER` and `PUSHOVER_TOKEN`).

```bash
cd 1_foundations/community_contributions/sebastian_arrejin/linkedin_twin
uv run app.py
```

Add `SHOW_ADMIN_TAB=true` to `.env` to see a tab with the database tables.
To add more knowledge, copy `knowledge/_template.md` to a new file without the leading underscore, or drop in a PDF.
