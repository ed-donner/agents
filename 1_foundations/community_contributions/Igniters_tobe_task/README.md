# Bio Agent — Self-Improving Career Assistant

A local, private, and modular career assistant that represents you professionally. It uses **RAG** (Retrieval-Augmented Generation) for accurate facts, a **SQL** backend for persistence, and a built-in **Evaluator** for self-improvement.

---

## Features

- **Local Intelligence**: Runs 100% locally via Ollama (No API keys or costs).
- **RAG System**: Ingests your LinkedIn PDF and summary for factual answering.
- **Self-Improving FAQ**: High-scoring answers are promoted to a cache to speed up repetitive questions.
- **Reflection Loop**: An LLM-as-judge scores every response; if it's below a 7/10, the agent "reflects" on feedback and retries.
- **Clean Architecture**: Modular Python structure with separated concerns (Config, DB, RAG, Tools, Agent, UI).

---

## Getting Started

### 1. Prerequisites

- **Ollama**: [Download and install Ollama](https://ollama.com).
- **Models**: Pull the two required models:
  ```bash
  ollama pull llama3.2        # Main Agent (3B)
  ollama pull llama3.1:8b     # Quality Evaluator (8B)
  ```

### 2. Installations

We recommend using `uv` for lightning-fast, sandboxed environment management:

```bash
# Install dependencies
uv pip install -r requirements.txt
```

### 3. Run the App

Start the chat interface:
```bash
uv run python app.py
```

---

## Project Structure

- `app.py`: Minimal entrypoint (Gradio UI).
- `agent.py`: Agent loop, tool dispatch, and reflection logic.
- `evaluator.py`: LLM-as-judge scoring system.
- `rag.py`: Knowledge base ingestion and retrieval.
- `database.py`: SQLite layer for FAQs and contact recording.
- `tools.py`: Tool definitions and schemas.
- `config.py`: Global settings and model parameters.
- `knowledge/`: Place your `Profile.pdf` and `summary.txt` here.

---

## How It Works

1. **User asks a question**.
2. **Agent checks the FAQ first** for a quick cached answer.
3. If not found, **RAG searches your documents** for the most relevant context.
4. An **Evaluator model (8B)** scores the draft answer for accuracy and professionalism.
5. If the score is low, the Agent **self-corrects** based on the feedback before showing the final response to you.
