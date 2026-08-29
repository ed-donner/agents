# Nicholas Dean - Week 2 (OpenAI Agents SDK)

The full Deep Research capstone: guardrail -> structured planner -> parallel search -> structured
writer -> email agent.

- `deep_research.py` - an input `@input_guardrail` screens the request; a Planner returns a
  structured `WebSearchPlan`; search agents run in parallel with `asyncio.gather` and the hosted
  `WebSearchTool`; a Writer returns a structured `ReportData`; an Email agent sends it via a
  `send_report` `@function_tool` (SendGrid if `SENDGRID_API_KEY` is set, else writes `report.md`).
  The whole run is wrapped in one `trace()`.
- `SUMMARY.md` - what I learned this week.

Run: `uv run python deep_research.py "your question"`
(needs `OPENAI_API_KEY`; `WebSearchTool` bills per search; `SENDGRID_API_KEY` optional).
