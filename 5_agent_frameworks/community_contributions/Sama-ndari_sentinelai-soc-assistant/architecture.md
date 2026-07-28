# Architecture Documentation

## Overview

SentinelAI (SOC Assistant) is an AI-augmented security log analyzer. It combines rule-based threat detection with LLM-powered incident reporting. Real SOC tools do not blindly feed raw logs to a model; this project follows that hybrid pattern.

## Core Design Principles

### 1. Hybrid detection
- Deterministic rules catch known patterns reliably and auditably
- LLM adds context, impact assessment, and recommendations

### 2. Privacy-first evidence
- Raw logs never leave the detection layer for LLM calls
- Only structured evidence summaries are sent to the model

### 3. Industry framing
- Each rule maps to MITRE ATT&CK tactics/techniques
- Reports match SOC ticket-style outputs (severity, attack type, actions)

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SOC Assistant                             │
├─────────────────────────────────────────────────────────────────┤
│  Log Input → Parsers (Auth / Nginx / JSON) → Normalized entries │
│                              ↓                                   │
│                     Detection Engine                             │
│         Brute Force | Suspicious IP | Frequency Anomaly          │
│                              ↓                                   │
│              Alerts → Evidence Aggregator → GPT analysis         │
│                              ↓                                   │
│              Incident Report → SQLite + Web dashboard            │
└─────────────────────────────────────────────────────────────────┘
```

## Detection Rules

| Rule | Description | MITRE ATT&CK |
|------|-------------|--------------|
| Brute Force | Failed logins from a single IP | T1110.001 |
| Suspicious IP | Multi-user targeting, scanner patterns | T1595, T1190 |
| Frequency Anomaly | Rate spikes, off-hours activity | T1498 |

## Project Layout (full repo)

```
app/
  main.py              # FastAPI entry
  config.py            # Settings
  models/              # LogEntry, Alert, Incident
  parsers/             # Auth, Nginx, JSON
  detection/           # Engine, aggregator, rules/
  llm/                 # OpenAI client, prompts, analyzer
  reports/             # Incident report builder
  database/            # SQLite + repositories
  api/                 # Routes and dependencies
templates/             # Web dashboard
data/samples/          # Sample attack logs
```

## Agent-Style Flow (Week 5 lens)

1. **Ingest** — accept file upload or pasted log content
2. **Normalize** — parsers produce structured `LogEntry` objects
3. **Detect** — rule engine emits `Alert`s with severity and MITRE IDs
4. **Aggregate** — evidence summary (IPs, users, time range, metrics)
5. **Reason** — LLM produces title, attack type, recommendations, FP likelihood
6. **Persist** — store incident; expose via API and dashboard

This is a staged pipeline rather than a single agent loop with tools, but it mirrors production agent patterns: structured stages, tool-like modules, and a final LLM reasoning step on reduced context.

## API Surface (full repo)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Analyze log content |
| POST | `/api/analyze/upload` | Upload and analyze file |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Incident details |
| PATCH | `/api/incidents/{id}/status` | Update status |
| GET | `/api/rules` | List detection rules |
| GET | `/api/health` | Health check |

## Extending

- New detection rule: subclass `DetectionRule` under `app/detection/rules/`
- New parser: subclass `BaseParser` under `app/parsers/`

## Tech Stack

- Python 3.11+, FastAPI, Pydantic v2
- OpenAI GPT-4o-mini
- SQLite via aiosqlite
- HTML + Tailwind CDN dashboard

## Full Source

https://github.com/Sama-ndari/sentinelai-soc-assistant
