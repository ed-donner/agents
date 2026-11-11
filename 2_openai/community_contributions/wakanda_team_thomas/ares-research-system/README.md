# ARES: Autonomous Research & Extraction System

A multi-agent deep research system built on the OpenAI Agents SDK. Uses hierarchical orchestration to plan, execute, and synthesize web research into structured Markdown reports.

## Architecture

```
User Query → Safety Guardrail → Research Architect (gpt-4o)
                                    ├── Web Specialist (gpt-4o-mini + Tavily)
                                    └── Report Editor (gpt-4o-mini)
                                            └── Notification Agent (Resend email)
```

## Setup

Add to your `.env`:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...      # Free: 1000 queries/month
RESEND_API_KEY=re_...        # Free: 3000 emails/month (optional)
```

## Usage

**Gradio UI:**
```bash
uv run 2_openai/community_contributions/wakanda_team_thomas/ares-research-system/app.py
```

**CLI:**
```bash
uv run 2_openai/community_contributions/wakanda_team_thomas/ares-research-system/main.py \
    --query "Latest breakthroughs in quantum computing"
```

## Features

- **Hierarchical orchestration**: Architect agent coordinates specialist agents as tools
- **Live web search**: Tavily API with recency prioritization
- **Structured output**: Pydantic-enforced reports with executive summary and citations
- **Safety guardrails**: Input validation blocks harmful queries
- **Human-in-the-loop**: Email delivery requires explicit approval
