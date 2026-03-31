"""Education policy-focused planner, search, and writer agents for OpenAI Agents SDK."""

from pydantic import BaseModel, Field
from agents import Agent, ModelSettings, WebSearchTool

HOW_MANY_SEARCHES = 5

PLANNER_INSTRUCTIONS = f"""You plan web searches for **global education policy** questions.

Given the user's query, output exactly {HOW_MANY_SEARCHES} search items. Bias queries toward:
- Ministry of Education or equivalent official government sites
- International organizations (e.g., UNESCO, OECD)
- Education reforms, curriculum standards, funding policies, and equity programs
- Provide context for why each search is relevant
If jurisdiction is not specified, include searches covering at least one country-level policy.
"""

class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search matters for the education question.")
    query: str = Field(description="Web search query string.")

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="Searches to answer the education policy question with traceable sources.")

planner_agent = Agent(
    name="EducationPlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)

SEARCH_INSTRUCTIONS = (
    "You research **education policy** using web search. Summarize what you find in 2–3 short paragraphs "
    "(under ~300 words). Focus on official reports, policy papers, or government announcements. "
    "If results are mostly news or blogs, indicate that. Note any uncertainties. "
    "Output only the summary—no preamble."
)

search_agent = Agent(
    name="EducationSearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

WRITER_INSTRUCTIONS = """You write a **structured education policy research brief**.

Include:
1. Clear scope statement (country or region, topic)
2. Sections: Overview; Key reforms and agencies; Timeline or status; Stakeholder perspectives; Evidence quality
3. A short **Disclaimer**: draft research only, verify with official sources

Use markdown headings. Be precise about what is **not confirmed**. Aim for 800–1500 words unless evidence is thin.
"""

class PolicyReportData(BaseModel):
    short_summary: str = Field(description="2–4 sentences for executives.")
    jurisdiction_scope: str = Field(description="Country/region or 'unspecified'.")
    key_instruments: str = Field(description="Markdown bullet list of named laws, programs, agencies, or reforms.")
    markdown_report: str = Field(description="Full markdown policy brief including disclaimer.")
    evidence_gaps: str = Field(description="What was not verified or missing.")
    follow_up_questions: list[str] = Field(description="Next research steps or official sources to check.")

writer_agent = Agent(
    name="EducationWriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=PolicyReportData,
)