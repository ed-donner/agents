from agents import Agent, ModelSettings
from pydantic import BaseModel, Field


class ResearchDimension(BaseModel):
    dimension: str = Field(description="The dimension of the research to be decomposed e.g features, pricing, market position, etc.")
    queries: list[str] = Field(description="The specific search queries for this dimension.")

class ResearchPlan(BaseModel):
    target_product: str = Field(description="The product or service that is the target of the research.")
    target_context_query: str = Field(description="Query to understand the target itself.")
    competitor_discovery_query: str = Field(description="Query to discover competitors of the target.")
    dimensions: list[ResearchDimension] = Field(description="The dimensions of the research to be decomposed.")

decomposer_instructions = """
You perform query decomposition for competitive intelligence research.

Given a product or company name, break the analysis into a structured research plan:

1. A target_context_query to understand what the product does, who it serves, and what
   category it belongs to.
2. A competitor_discovery_query to find its direct competitors.
3. A set of research dimensions -- the specific angles to investigate for every competitor.

Always include these core dimensions:
- Features & capabilities (what the product does)
- Pricing & plans (free tier, paid tiers, enterprise)
- Target audience & market position (who uses it, market share)

Add 1-2 additional dimensions when relevant to the product category, such as:
- Integrations & ecosystem (for SaaS/developer tools)
- User experience & design (for consumer products)
- Performance & reliability (for infrastructure/cloud)

For each dimension, generate 2-3 specific, searchable queries that would work well in a web
search engine. Write queries as a real user would type them, not as full sentences.
Good: "Notion pricing plans 2026"
Bad: "What are the different pricing plans offered by Notion?"

Aim for 4-5 dimensions total to keep the research focused.
"""

DecomposerAgent = Agent(
    name="Decomposer Agent",
    instructions=decomposer_instructions,
    output_type=ResearchPlan,
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        max_tokens=1000,
    )
)

from agents import Agent, ModelSettings, WebSearchTool
from pydantic import BaseModel, Field


class Competitor(BaseModel):
    name: str = Field(description="The name of the competitor.")
    url: str = Field(description="The URL of the competitor.")
    reason: str = Field(description="The reason why this competitor is important.")

class CompetitorList(BaseModel):
    competitors: list[Competitor] = Field(description="The list of competitors.")

scout_instructions = """
You are a competitive intelligence scout. Given a target product or company, your job is to
identify its most relevant competitors using web search.

Search for the target product first to understand what it does and what market it operates in.
Then search for its direct competitors -- products that serve the same audience and solve the
same core problem.

Prioritize competitors by market relevance: established players and fast-growing challengers
matter most. Aim for 3-5 competitors. Exclude tangentially related products that don't truly
compete for the same users.

For each competitor, provide its official website URL and a one-sentence reason explaining
why it competes with the target.
"""

ScoutAgent = Agent(
    name="Scout Agent",
    instructions=scout_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    output_type=CompetitorList,
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        max_tokens=1000,
        tool_choice="required",
    )
)


researcher_instructions = """
You are a competitive research agent that deep-dives into a single competitor.

You will receive a competitor name along with specific research dimensions to investigate
(e.g. features, pricing, market position).

For each research dimension, use the web search tool to gather current, factual information
about the competitor. Synthesize your findings into a concise summary of 2-3 paragraphs
(less than 300 words total).

Focus on capturing concrete facts: product capabilities, pricing tiers, target audience,
notable strengths and weaknesses. Write succinctly -- this will be consumed by an analyst
synthesizing a competitive comparison, so capture the essence and skip any fluff.

Do not include any commentary beyond the summary itself.
"""

ResearcherAgent = Agent(
    name="Researcher Agent",
    instructions=researcher_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        tool_choice="required",
    ),
)
