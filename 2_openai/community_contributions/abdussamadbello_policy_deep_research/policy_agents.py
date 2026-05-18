"""Policy-focused planner, search, and writer agents for OpenAI Agents SDK."""

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings, WebSearchTool

HOW_MANY_SEARCHES = 5

PLANNER_INSTRUCTIONS = f"""You plan web searches for **government and public policy** questions.

Given the user's query, output exactly {HOW_MANY_SEARCHES} search items. Bias queries toward:
- Official government sites (e.g. agency domains, legislature, gazette/register language)
- Primary legal or regulatory instruments (acts, codes, rules, guidance) where relevant
- Neutral factual phrases, not only opinion headlines

If the query omits jurisdiction, include at least one search that narrows country or level (federal/state/local)."""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the policy question.")
    query: str = Field(description="Web search query string.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="Searches to run to answer the policy question with traceable sources."
    )


planner_agent = Agent(
    name="PolicyPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

SEARCH_INSTRUCTIONS = (
    "You research **public policy** using web search. Summarize what you find in 2–3 short paragraphs "
    "(under ~300 words). Prefer facts tied to named laws, agencies, dates, or official pages. "
    "If results are mostly news or blogs, say so. Note uncertainty (e.g. 'effective date not confirmed'). "
    "Output only the summary—no preamble."
)

search_agent = Agent(
    name="PolicySearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

WRITER_INSTRUCTIONS = """You write a **policy research brief** (not legal advice).

You receive the user's question and raw search summaries. Produce:
1. A clear scope statement (jurisdiction and topic).
2. Sections: Overview; Key instruments & actors; Timeline or status (if known); Stakeholder angles (brief); Evidence quality (official vs secondary).
3. A short **Disclaimer** paragraph: draft for research only, verify with qualified counsel and primary legal texts.

Use markdown headings. Be precise about what is **not** established from the evidence. Aim for roughly 800–1500 words unless the evidence is thin—then say so and stay shorter."""


class PolicyReportData(BaseModel):
    short_summary: str = Field(description="2–4 sentences for executives.")
    jurisdiction_scope: str = Field(
        description="Stated jurisdiction/level or 'unspecified' if unclear."
    )
    key_instruments: str = Field(
        description="Markdown bullet list of named laws, rules, agencies, or programs mentioned."
    )
    markdown_report: str = Field(description="Full markdown policy brief including disclaimer section.")
    evidence_gaps: str = Field(
        description="What was not verified or missing from the search material."
    )
    follow_up_questions: list[str] = Field(
        description="Concrete next research steps or official sources to check."
    )


writer_agent = Agent(
    name="PolicyWriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=PolicyReportData,
)
