# Autonomous SDR Agent (Week 2)

Sales Development Representative agent that writes outbound email, classifies replies, and routes to escalate / rebut / close.

Week 2 patterns: multi-agent orchestration, tools (SendGrid), handoffs, conversation memory.

## Flow

Outbound writer → SendGrid → reply classifier → decision engine → escalate / follow-up / close

## Setup

```bash
cd 2_openai/community_contributions/Sama-ndari_autonomous-sdr-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (do not commit):

```
OPENAI_API_KEY=...
SENDGRID_API_KEY=...
```

## Run

Open `sdr_agent.ipynb` and run all cells.

Full project (optional): https://github.com/Sama-ndari/autonomous-sdr-agent

## Author

[Sama-ndari](https://github.com/Sama-ndari) — https://www.samandari.dev
