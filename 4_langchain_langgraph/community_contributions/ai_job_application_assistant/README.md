# AI Job Application Assistant

A **LangGraph** workflow with a **Gradio** UI. You paste a job description and your CV; the graph parses the role, classifies it (technical / creative / management), pulls company context via **Google Serper**, tailors the CV, writes a cover letter, and runs an **LLM evaluator** that can loop revisions (up to three). It then **interrupts for human review**: approve (optionally edit the letter) or reject.

**Approve & send** does not email anyone—it prints the final cover letter and tailored CV to the terminal.

## Environment

| Variable | Purpose |
|----------|---------|
| `OPENROUTER_API_KEY` | Chat model (`gpt-4o-mini` through OpenRouter) |
| `SERPER_API_KEY` | Company research searches |

Use the repo root environment (e.g. `requirements.txt` / `.env`) or install `langgraph`, `langchain-openai`, `langchain-community`, `gradio`, `python-dotenv`, and `pydantic`.

## Run

```bash
uv run app.py
```