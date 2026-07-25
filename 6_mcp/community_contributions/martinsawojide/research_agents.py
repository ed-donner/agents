"""Planner, search, writer, and email agent definitions for deep research."""

from pydantic import BaseModel, Field

from agents import Agent, ModelSettings

from model_config import gpt_4o_mini_model

# --- Planner ---

HOW_MANY_SEARCHES = 5

PLANNER_INSTRUCTIONS = (
    f"You are a helpful research assistant. Given a query, come up with a set of web searches "
    f"to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."
)


class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query.")
    query: str = Field(description="The search term to use for the web search.")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model=gpt_4o_mini_model,
    output_type=WebSearchPlan,
)

# --- Search (MCP Tavily) ---

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you use your Tavily web search tool "
    "for that term and produce a concise summary of the results. The summary must be 2-3 paragraphs "
    "and less than 300 words. Capture the main points. Write succinctly; complete sentences and "
    "perfect grammar are not required. This will be consumed by someone synthesizing a report, so "
    "capture the essence and ignore fluff. Do not include any additional commentary other than "
    "the summary itself."
)


def build_search_agent(mcp_servers: list) -> Agent:
    return Agent(
        name="Search agent",
        instructions=SEARCH_INSTRUCTIONS,
        tools=[],
        mcp_servers=mcp_servers,
        model=gpt_4o_mini_model,
        model_settings=ModelSettings(tool_choice="required"),
    )

# --- Writer ---

WRITER_INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)


class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings.")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: list[str] = Field(description="Suggested topics to research further")


writer_agent = Agent(
    name="WriterAgent",
    instructions=WRITER_INSTRUCTIONS,
    model=gpt_4o_mini_model,
    output_type=ReportData,
)

# --- Email (MCP SendGrid) ---

EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the
report converted into clean, well presented HTML with an appropriate subject line."""


def build_email_agent(mcp_servers: list) -> Agent:
    return Agent(
        name="Email agent",
        instructions=EMAIL_INSTRUCTIONS,
        tools=[],
        mcp_servers=mcp_servers,
        model=gpt_4o_mini_model,
    )
