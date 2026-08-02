# CodePhoenix (Week 3)

CrewAI sequential crew that diagnoses broken Python, researches a fix, verifies execution (Docker-safe mode), and notifies via Pushover.

Week 3 patterns: multi-agent crew, YAML agent/task config, tools (Serper, file R/W, code execution), structured output.

## Agents

1. Investigator — read + Serper research
2. Engineer — write fix + sandboxed code execution
3. Manager — validate + push notification

## Setup

```bash
cd 3_crewai/community_contributions/Sama-ndari_code_phoenix
uv sync
# or: pip install crewai[tools] pydantic requests
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
SERPER_API_KEY=...          # optional but recommended
PUSHOVER_USER=...           # optional
PUSHOVER_TOKEN=...
```

Docker Desktop recommended if `code_execution_mode="safe"` in `crew.py`.

## Run

```bash
uv run run_crew
# or: python -m code_phoenix.main
```

Input sample: `broken_script.py`. Example fixed output: `fixed_script.py`.

Full project (optional): https://github.com/Sama-ndari/code-phoenix

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
