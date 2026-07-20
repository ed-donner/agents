# Repo onboarding Sidekick

 **Sidekick** agent that helps developers understand a **local** codebase.  tools are **read-only filesystem** helpers (no browser, no arbitrary shell).

## What you get

- **Worker** (configurable LLM + tools) explores the repo you choose and answers onboarding-style questions.
- **Evaluator** checks the last answer against **success criteria** (editable in the UI). If criteria are not met, the worker gets feedback and tries again until success, user input is needed, or the graph ends per evaluator policy.
- **Gradio UI** for repository path, optional success criteria, and chat.

Default success criteria ask for: grounded file paths, a short architecture summary, how to run/test if discoverable, where a newcomer would change code, and one small first-contribution idea.

## LLM (OpenRouter only)

All chat calls go through [OpenRouter](https://openrouter.ai/) using `ChatOpenAI` with OpenRouter’s `base_url` and `OPENROUTER_API_KEY` (see `repo_onboarding_sidekick.py`).

Set `OPENROUTER_API_KEY` (required). Optional: `OPENROUTER_BASE_URL`, `OPENROUTER_MODEL`, `OPENROUTER_HTTP_REFERER`, `OPENROUTER_APP_TITLE`. See `.env.example`.

```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-v1-...
python app.py
```

## Tools (read-only)

All paths are resolved **inside** the chosen repository root; attempts to escape the root are rejected.

- **list_repo_directory** — list a relative directory (use `.` for root).
- **read_repo_file** — read a text file with size limits; skips obvious binary content.
- **search_repo_text** — substring search with optional filename glob; skips heavy dirs such as `.git`, `node_modules`, `__pycache__`, and common virtualenv folders.
- **repo_summary** — root path, top-level names, and presence of common manifest files.

