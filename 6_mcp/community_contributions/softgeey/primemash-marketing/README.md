# Primemash Technologies — Autonomous Marketing Agent System

> "Automating African Businesses, Amplifying Growth"

A fully autonomous digital marketing system powered by the **OpenAI Agents SDK** with specialist agent handoffs, **OpenRouter** (Claude/GPT-4o), and a **Next.js 14** dashboard with Google OAuth.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Next.js 14 Dashboard                   │
│  Google OAuth · Dashboard · Posts · Campaigns ·     │
│  Analytics · Agent Chat                             │
└─────────────────┬───────────────────────────────────┘
                  │ REST (JWT)
┌─────────────────▼───────────────────────────────────┐
│              FastAPI Backend                        │
│  /api/agent/run · /api/posts · /api/campaigns ·     │
│  /api/analytics · APScheduler (cron jobs)           │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         OpenAI Agents SDK Orchestration             │
│                                                     │
│  MarketingOrchestrator                              │
│    ├── ContentWriterAgent  (generate posts)         │
│    ├── PublisherAgent      (post to platforms)      │
│    ├── CampaignPlannerAgent (create campaigns)      │
│    └── AnalyticsAgent      (report & insights)      │
└──────┬──────────┬──────────┬────────────────────────┘
       │          │          │
  LinkedIn     Twitter   Instagram
  (UGC API)  (Tweepy)  (Meta Graph)
                  │
             Supabase DB
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Supabase account (free tier works)
- OpenRouter account
- Google Cloud Console project (for OAuth)
- LinkedIn Developer App, Twitter Developer App, Meta Developer App

---

### Step 1 — Database Setup

1. Go to [supabase.com](https://supabase.com) → create a new project
2. Open **SQL Editor** → paste the full contents of `supabase_schema.sql` → Run
3. Copy your **Project URL** and **service_role** key from Settings → API

---

### Step 2 — Backend Setup

```bash
cd primemash-marketing

# Install dependencies with uv
uv sync

# Copy and fill in your credentials
cp .env.example .env
# Edit .env with your real keys (see "Credentials" section below)

# Start the API server
python main.py --serve
# → Running on http://localhost:8000
```

---

### Step 3 — Frontend Setup

```bash
cd primemash-marketing/frontend

npm install

# Copy and fill in frontend credentials
cp .env.example .env.local
# Edit .env.local

npm run dev
# → Running on http://localhost:3000
```

---

### Step 4 — Verify

1. Visit `http://localhost:3000` → redirects to sign-in
2. Click **Continue with Google** → lands on Dashboard
3. Click **Run Daily Posts** → triggers agents
4. Go to **Agent** page → type any marketing task

---

## Credentials Guide

### OpenRouter
1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Create an API key → paste into `OPENROUTER_API_KEY`
3. Default model: `anthropic/claude-3.5-sonnet` (change in `.env` to `openai/gpt-4o` etc.)

### Google OAuth
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create project → Enable **Google+ API**
3. Credentials → OAuth 2.0 Client ID (Web application)
4. Authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
5. Copy Client ID and Secret into both `.env` files

### LinkedIn
1. Go to [linkedin.com/developers](https://www.linkedin.com/developers/)
2. Create App → request `w_member_social` permission
3. Generate Access Token via OAuth 2.0 flow
4. Find your Person URN: `https://api.linkedin.com/v2/me` (with your token)

### X (Twitter)
1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create Project + App → enable **Read and Write** permissions
3. Generate all 4 keys: API Key, API Secret, Access Token, Access Token Secret

### Instagram (Meta)
1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create App → Add **Instagram Graph API** product
3. Connect Instagram Business Account
4. Generate a Long-Lived User Access Token
5. Get your Instagram Business Account ID from the API

### Supabase
- `SUPABASE_URL`: your project URL (e.g. `https://xxx.supabase.co`)
- `SUPABASE_SERVICE_KEY`: service_role key (Settings → API → service_role)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: anon/public key

---

## Autonomous Scheduling

The backend scheduler runs automatically when the API starts:

| Job | Schedule | What it does |
|-----|----------|-------------|
| Daily content | Mon–Fri 8AM WAT | Generates + publishes 1 post per platform |
| Publish scheduled | Every 15 min | Publishes any posts with `status=scheduled` |
| Weekly report | Monday 9AM WAT | AI analytics report in logs |

---

## Agent Commands (Agent Chat Page)

Type natural language tasks like:

- `Post today's content on all 3 platforms`
- `Create a 14-day campaign targeting Lagos e-commerce businesses`
- `Generate a LinkedIn post about WhatsApp automation for retail`
- `Show analytics report with recommendations`
- `Generate a Twitter tip about invoice automation`

---

## CLI Usage

```bash
# Interactive mode
python main.py

# Single task
python main.py "Post today's content to all platforms"

# Daily run
python main.py --daily

# Analytics report
python main.py --analytics

# Start API server
python main.py --serve
```

---

## Project Structure

```
primemash-marketing/
├── main.py                     # CLI entry point
├── pyproject.toml              # Python deps (uv)
├── .env.example                # Backend env template
├── supabase_schema.sql         # DB setup (run once)
│
├── src/
│   ├── agents/
│   │   └── marketing_team.py   # All 5 agents + orchestrator
│   ├── tools/
│   │   ├── content_generator.py # OpenRouter content generation
│   │   └── publishers.py        # LinkedIn, Twitter, Instagram
│   ├── lib/
│   │   ├── brand_context.py     # Primemash brand knowledge
│   │   ├── database.py          # Supabase queries
│   │   └── scheduler.py         # APScheduler cron jobs
│   └── api.py                   # FastAPI routes
│
└── frontend/
    ├── app/
    │   ├── api/auth/[...nextauth]/route.ts
    │   ├── auth/signin/page.tsx
    │   ├── dashboard/           # Overview + quick actions
    │   ├── posts/               # All posts, generate new
    │   ├── campaigns/           # Create + view campaigns
    │   ├── analytics/           # Stats + AI report
    │   └── agent/               # Direct agent chat
    ├── components/
    │   ├── layout/Sidebar.tsx
    │   ├── layout/AuthProvider.tsx
    │   └── ui/                  # PostCard, StatCard
    ├── lib/api.ts               # Backend API client
    └── types/index.ts           # Shared TypeScript types
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agents | OpenAI Agents SDK (handoffs, tools) |
| LLM | OpenRouter → Claude 3.5 Sonnet (or any model) |
| Backend | FastAPI + APScheduler |
| Frontend | Next.js 14 App Router + Tailwind CSS |
| Auth | NextAuth.js + Google OAuth |
| Database | Supabase (PostgreSQL) |
| LinkedIn | LinkedIn UGC Posts API |
| Twitter | Tweepy (OAuth 1.0a) |
| Instagram | Meta Graph API |
| Package mgr | uv (Python) + npm (Node) |
