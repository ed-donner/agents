# Trust-Aware Deep Research

A refactored research agent with source quality controls and evidence-backed claims.

## Quick Start

```bash
./deep_research_lab
python app.py
```

## Architecture

```text
User Topic
    ↓
IntakeAgent → Follow-up Questions → User Answers → Locked Brief
    ↓
PlannerAgent → Search Strategy (with source policy)
    ↓
SearchExecutor → Raw Sources + Snippets (deduplicated, tier-tagged)
    ↓
SynthesizerAgent → Claim Ledger (evidence-backed assertions)
    ↓
WriterAgent → Report (constrained to ledger only)
    ↓
EmailAgent → HTML email (optional)
```

## Key Features

### Source Quality Policy

Treats the internet as adversarial:

1. **PRIMARY**: Papers, official docs, government data (highest trust)
2. **SECONDARY**: Reputable news, established analysts
3. **VENDOR**: Company material (labeled as such)
4. **OPINION**: Blogs (framing only)
5. **EXCLUDED**: Social media (not used)

### Claim Ledger

Every factual assertion must map to evidence:

- **Claim**: Single assertion
- **Evidence**: Supporting quote/data
- **Source**: URL + tier
- **Confidence**: low/medium/high
- **Notes**: Caveats, conflicts, bias

The writer cannot invent facts outside the ledger.

## Files

| File | Purpose |
|------|---------|
| `models.py` | Pydantic schemas for all data structures |
| `intake_agent.py` | Generates questions, produces research brief |
| `planner_agent.py` | Creates search strategy with source policy |
| `search_executor.py` | Executes searches, tags source tiers |
| `synthesizer_agent.py` | Builds claim ledger from evidence |
| `writer_agent.py` | Writes report constrained to ledger |
| `email_agent.py` | Sends formatted HTML email |
| `research_manager.py` | Orchestrates the full workflow |
| `app.py` | Multi-step Gradio UI |

## Configuration

Update `email_agent.py` with your SendGrid credentials:

- Set `SENDGRID_API_KEY` environment variable
- Update sender/recipient emails in the file

## Credits

Based on the deep_research example from `2_openai/deep_research/`, extended with:

- Intake phase with clarifying questions
- Source quality policy
- Claim ledger for accountability
- Multi-step UI
