# SentinelAI — SOC Assistant (Week 5)

Hybrid Security Operations Center assistant: deterministic detection rules first, then LLM reasoning for incident reports. Built with FastAPI, OpenAI, and MITRE ATT&CK mapping.

Week 5 angle: agent-style pipeline (parse → detect → aggregate evidence → LLM analyze → report), privacy-first (raw logs never sent to the model), structured tool-like stages instead of a blind chat dump.

## Pipeline

Log input → Parsers (auth / nginx / JSON) → Detection engine (brute force, suspicious IP, frequency) → Evidence aggregator → GPT analysis → Incident report → SQLite

## Why lean contribution?

Full source is larger than a typical community PR. Per course guidance, this folder documents the design; complete runnable code is in the standalone repo.

Full project: https://github.com/Sama-ndari/sentinelai-soc-assistant

## Setup (full repo)

```bash
git clone https://github.com/Sama-ndari/sentinelai-soc-assistant.git
cd sentinelai-soc-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
uvicorn app.main:app --reload
# open http://localhost:8000
```

Local deps mirror: see `requirements.txt` in this folder.

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
