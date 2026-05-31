from agents import Agent, ModelSettings
from deep_research_agents import DecomposerAgent, ScoutAgent, ResearcherAgent
from reporter_agent import ReporterAgent
from pydantic import BaseModel, Field
from agents import Agent, GuardrailFunctionOutput, ModelSettings, Runner, WebSearchTool, input_guardrail


class ProductCheckOutput(BaseModel):
    reasoning: str = Field(description="The reasoning behind the decision.")
    is_a_valid_product: bool = Field(description="Whether the entity contained in the user's message is a valid product or service.")
    web_search_results: list[str] = Field(description="The web search results for the product.")

product_guardrail_instructions = """
You validate whether the user's input refers to a real product, service, or company that can
be competitively analyzed.

Search the web for the entity mentioned. It is VALID if it is a recognizable product, SaaS
tool, company, or service with an active web presence (official website, app store listing,
or widely covered in tech/business media).

It is INVALID if:
- The input is a task or instruction (e.g. "Build a website from scratch", "Write a blog post")
- The input is a generic concept or category (e.g. "productivity", "website builder", "AI")
- The input is gibberish, a person's name, or a question
- No credible web results confirm it as an actual named product or company
- It refers to something that cannot have competitors (e.g. a nonprofit cause, a country)

The input must be a specific, named product or company (e.g. "Notion", "Shopify", "Tesla").
"Build a website" is a task, not a product -- INVALID.
"Website builders" is a category, not a product -- INVALID.
"Wix" is a specific product -- VALID.

Include the key web search results you used to make your decision in your output.
Be fast -- this is a gatekeeping check, not deep research.
"""

ProductGuardrailAgent = Agent(
    name="Product Guardrail Agent",
    instructions=product_guardrail_instructions,
    tools=[WebSearchTool(search_context_size="low")],
    output_type=ProductCheckOutput,
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required")
)

@input_guardrail
async def product_guardrail(ctx, agent, message):
    result = await Runner.run(ProductGuardrailAgent, message, context=ctx.context)
    output = result.final_output
    return GuardrailFunctionOutput(output_info={"output": output}, tripwire_triggered=not output.is_a_valid_product)

decomposer_tool = DecomposerAgent.as_tool(
    tool_name="decompose_query",
    tool_description="Break a product/company name into a structured research plan with dimensions and search queries.",
)

scout_tool = ScoutAgent.as_tool(
    tool_name="scout_competitors",
    tool_description="Identify the top 3-5 direct competitors for a given product using web search.",
)

researcher_tool = ResearcherAgent.as_tool(
    tool_name="research_competitor",
    tool_description="Deep-dive into a single competitor. Input MUST include the competitor name AND the research dimensions to investigate (e.g. features, pricing, market position). Call once per competitor.",
)

manager_instructions = """
You are the orchestrator of a competitive intelligence pipeline. Given a product or company
name, you coordinate three phases of research before handing off to an analyst.

Follow these steps in order:

1. DECOMPOSE: Call decompose_query with the user's input to get a structured research plan
   containing the target product, discovery queries, and research dimensions.

2. SCOUT: Call scout_competitors with the target product name and its context to identify
   the top direct competitors.

3. RESEARCH: For each competitor returned by the scout, call research_competitor. The input
   to each call MUST include both the competitor name AND the full list of research
   dimensions from the plan. For example:
   "Competitor: Evernote. Research dimensions: Features & capabilities, Pricing & plans,
    Target audience & market position, Integrations & ecosystem"
   Call this tool once per competitor -- do not skip any.

4. HAND OFF: Once all competitors have been researched, hand off to the Analyst. In your
   handoff message, include ALL of the following so the Analyst has full context:
   - The target product name and what it does
   - The list of competitors that were researched
   - The research dimensions that were investigated
   - The full research summary for each competitor

Do not write the analysis yourself. Your job is to gather information and pass it along.
"""

ManagerAgent = Agent(
    name="Manager Agent",
    instructions=manager_instructions,
    tools=[decomposer_tool, scout_tool, researcher_tool],
    handoffs=[ReporterAgent],
    input_guardrails=[product_guardrail],
    model="gpt-4o-mini",
    model_settings=ModelSettings(
        max_tokens=4000,
    ),
)
