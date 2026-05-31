from pydantic import BaseModel
from agents import Agent, ModelSettings, WebSearchTool

SEARCH_COUNT = 5


class ClarifiedQuery(BaseModel):
    refined: str
    angles: list[str]


class SearchTask(BaseModel):
    term: str
    rationale: str


class ResearchPlan(BaseModel):
    tasks: list[SearchTask]


class TechVerdict(BaseModel):
    tldr: str
    recommendation: str
    strengths: list[str]
    red_flags: list[str]
    alternatives: list[str]
    full_report: str


clarifier = Agent(
    name="clarifier",
    instructions=(
        "Take a vague question about a technology and sharpen it. "
        "If someone just says 'Kubernetes', figure out the angle "
        "small team eval? migration? scaling concerns? "
        "Output a tighter version and 3-4 angles to investigate."
    ),
    model="gpt-4o-mini",
    output_type=ClarifiedQuery,
)

planner = Agent(
    name="search-planner",
    instructions=(
        f"Plan exactly {SEARCH_COUNT} web searches to evaluate a technology.\n"
        "Target real practitioner experiences (reddit, HN, dev blogs), "
        "known issues, benchmark comparisons, alternatives people switched to.\n"
        "Skip marketing pages and generic listings."
    ),
    model="gpt-4o-mini",
    output_type=ResearchPlan,
)

searcher = Agent(
    name="web-searcher",
    instructions=(
        "Search the web and summarize in 2-3 paragraphs, under 250 words. "
        "Prioritize real experiences over official docs. Include specifics — "
        "version numbers, dates, concrete complaints or praise. "
        "If results are mostly marketing say so. Just the summary."
    ),
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

analyst = Agent(
    name="tech-analyst",
    instructions=(
        "Write an honest tech evaluation from the research provided.\n\n"
        "Structure: Executive Summary, What It Does Well "
        "Red Flags & Gotchas, Alternatives Worth Considering, Verdict.\n\n"
        "Markdown, 800-1500 words. If evidence is weak, say so and keep it short. "
        "Write like you're advising a friend on an architecture decision."
    ),
    model="gpt-4o-mini",
    output_type=TechVerdict,
)
