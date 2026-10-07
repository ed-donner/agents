# Financial Researcher Crew: Gemini + DuckDuckGo (free tier only)

The week 3 Financial Researcher crew, changed so it runs entirely on **free services with no credit card**:

| Course version | This version | Why |
|---|---|---|
| OpenAI models | **Google Gemini** (`gemini-3.5-flash-lite`) | Free API key from Google AI Studio |
| `SerperDevTool` | **DuckDuckGo search** via [`ddgs`](https://pypi.org/project/ddgs/) | No signup, no API key |

**Crew tracing** is turned on (`tracing=True`), so you can look at each agent step, LLM call and tool call after a run.

## What the crew does

You enter a company name, and two agents run in sequence:

1. **Researcher** searches the web and news for the company's current status, history, challenges, recent news and outlook.
2. **Analyst** turns the research into a report with an executive summary → `output/report.md`

## Setup

1. Create a free Gemini key at [Google AI Studio](https://aistudio.google.com/apikey).
2. Copy `.env.example` to `.env` and add the key:

   ```
   GEMINI_API_KEY=your-gemini-key
   ```

3. Install and run, then enter a company name when asked:

   ```bash
   crewai install
   crewai run
   ```

At the end of the run, CrewAI asks whether you want to view the execution trace.

## Implementation notes

- `pyproject.toml` needs `crewai[tools,google-genai]`. Without the `google-genai` extra, CrewAI fails with `Google Gen AI native provider not available`.
- `tools/search_tool.py` combines DuckDuckGo news and web results. If either search fails or finds nothing, the error goes back to the agent as text instead of crashing the crew.
- `max_rpm=12` on the Crew keeps it under the Gemini free tier limit of about 15 requests per minute. Every tool call is an extra LLM call, so the researcher can go over the limit. With this setting, CrewAI waits instead of failing with `429 RESOURCE_EXHAUSTED`.
- `main.py` passes today's full date as `current_date`, so the agents look for news as of today, not just the current year.

Contributed by Paresh Tahiliani.
