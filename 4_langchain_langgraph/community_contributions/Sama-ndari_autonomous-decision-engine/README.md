# Autonomous Decision Engine (Week 4)

LangGraph human-in-the-loop decision system. Every request is risk-scored before action: AUTONOMOUS, TOOLS, HUMAN, or STOP.

Week 4 patterns: StateGraph, conditional edges, structured outputs (Pydantic), checkpoint memory, ToolNode, HITL pause/resume.

## Decision paths

| Path | When |
|------|------|
| AUTONOMOUS | Low risk — execute directly |
| TOOLS | Medium risk — use search/browser tools with oversight |
| HUMAN | Higher risk — pause for confirmation |
| STOP | Too risky — refuse with explanation |

## Pipeline

User request → Task Analyzer → Risk Evaluator → Router → Worker / Tools / Human / Refusal → Quality Evaluator → done or retry/escalate

## Why lean contribution?

Full source is larger than a typical community PR. Per course guidance, this folder documents the design; complete runnable code is in the standalone repo.

Full project (optional): https://github.com/Sama-ndari/autonomous-decision-engine

## Setup (full repo)

```bash
git clone https://github.com/Sama-ndari/autonomous-decision-engine.git
cd autonomous-decision-engine
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY
python -m app.main
```

Local deps mirror: see `requirements.txt` in this folder.

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
