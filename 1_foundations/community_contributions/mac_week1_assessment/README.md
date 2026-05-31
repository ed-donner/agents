# Week 1 assessment — career chatbot extension

This folder submits the **Week 1 Lab 4 exercise** (and ties in patterns from Labs 3–4):

| Requirement | Implementation |
|-------------|----------------|
| Tool use + agent loop | `lookup_faq`, `record_user_details`, `record_unknown_question` with a `while` loop until the model finishes (no dangling tool calls). |
| FAQ / knowledge base | SQLite file `faq_assessment.db` (auto-created with seed rows; extend or replace in code). `lookup_faq` matches the user question to stored Q&A via a small structured LLM step. |
| Evaluator + retry | Pydantic `Evaluation` via `parse`; one automatic retry if the reply fails the check (Lab 3 pattern). |
| Optional Pushover | Same env vars as the course (`PUSHOVER_USER`, `PUSHOVER_TOKEN`); no-op print if unset. |

## Run locally

From the **repository root** (where `.venv` lives):

```bash
uv run python 1_foundations/community_contributions/mac_week1_assessment/week1_career_assessment.py
```

Put your **`1_foundations/me/linkedin.pdf`** and **`1_foundations/me/summary.txt`** in place (replace Ed’s samples with your own for a real deployment).

Set `OPENAI_API_KEY` in `.env`. Personalize `self.name` in `CareerBot.__init__` in `week1_career_assessment.py` before opening a PR.

## PR to the course repo

Fork [ed-donner/agents](https://github.com/ed-donner/agents), push your branch to **your fork**, then open a pull request against `ed-donner/agents` `main` with only your `community_contributions/...` folder (as in the course resources).
