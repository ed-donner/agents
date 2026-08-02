# AI Operations Manager Agent (Week 2)

Virtual boardroom orchestrator: breaks a business task into parallel Finance / HR / Engineering experts, then consolidates an executive report.

Week 2 patterns: orchestration, parallel agents (map-reduce), tools, structured handoffs.

## Flow

Ops Manager → parallel experts → reporting agent → final report (+ log / file / notify tools)

## Setup

```bash
cd 2_openai/community_contributions/Sama-ndari_ai-operations-manager-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
```

## Run

Open `ops_manager.ipynb` and run all cells.

Full project (optional): https://github.com/Sama-ndari/ai-operations-manager-agent

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
