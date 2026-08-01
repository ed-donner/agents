# Autonomous Scholarship Agent (Week 2)

OpenAI Agents SDK project: research a university, draft scholarship emails with multiple writers, apply input guardrails, pick the best draft, and send via SendGrid.

Matches Week 2 themes: agents, tools, handoffs, guardrails, deep research.

## Pipeline

1. Deep research planner + web search
2. Input guardrails (no fake professors / unsafe claims)
3. Three writers (Formal / Motivational / Concise)
4. Manager selects best draft
5. Email manager → SendGrid

## Setup

```bash
cd 2_openai/community_contributions/Sama-ndari_autonomous-scholarship-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
SENDGRID_API_KEY=...
# verified sender email as used in the notebook
```

## Run

Open `scholarship_agent.ipynb` and run all cells.

Full project (optional): https://github.com/Sama-ndari/autonomous-scholarship-sdr-agent

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
