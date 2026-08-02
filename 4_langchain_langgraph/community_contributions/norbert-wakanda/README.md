# Week 4 Project - Meeting Guide Agent

This project builds a LangGraph agent that prepares a meeting guide for bootcamp check-ins.
It fetches today's calendar events, inspects recently modified files, drafts a meeting guide,
and emails it to the user.

## Requirements

- Python dependencies from the bootcamp environment (LangGraph, LangChain, OpenAI, Google APIs, SendGrid)
- Environment variables configured:
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (optional, default: `gpt-4o-mini`)
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_SECRET_KEY`
  - `SENDGRID_API_KEY`

## Run

From this folder:

```bash
python app.ipynb
```

The agent will:
1. Fetch today's events from Google Calendar
2. Read recently modified Python files in the project directory (last 24 hours)
3. Draft a meeting guide tailored to the meeting type
4. Email the guide
