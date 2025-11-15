from agents import Runner, gen_trace_id

from product_agents import (
    MarketResearcherAgent,
    MarketResearchReport,
    IdeaCritiquerAgent,
    IdeaCritiqueReport,
    ProductManagerAgent,
    Schedule,
)


class ProductPlanner:
    """Entrypoint for building product planning agents."""

    def __init__(self):
        self.market_researcher_agent = MarketResearcherAgent()
        self.product_manager_agent = ProductManagerAgent()

    async def run(self, query: str):
        trace_id = gen_trace_id()
        print(
            f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
        )
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
        market_report = await self.conduct_market_research(query)
        yield "Market research complete, starting idea critique..."

        critique_report = await self.critique_idea(query, market_report)
        yield "Idea critique complete, starting product planning..."

        product_plan = await self.plan_product(query, market_report, critique_report)
        yield "Product planning complete."

        final_output = f"""
        {market_report}
        {critique_report}
        {product_plan}
        """

        yield final_output

    async def conduct_market_research(self, query: str) -> MarketResearchReport:
        """Conduct market research for the given product idea"""

        print("Starting market research...")
        result = await Runner.run(
            self.market_researcher_agent.agent_instance,
            f"Product Idea: {query}",
        )

        print("Performing research on the market...")
        return result.final_output_as(MarketResearchReport)

    async def critique_idea(
        self, idea: str, market_research_report: MarketResearchReport
    ) -> IdeaCritiqueReport:
        """Plan the product development schedule based on market research."""
        self.idea_critiquer_agent = IdeaCritiquerAgent(
            market_research_report=market_research_report
        )

        print("Critiqing the product idea...")
        result = await Runner.run(
            self.idea_critiquer_agent.agent_instance,
            f"Product Idea: {idea}",
        )
        print("Idea critiqued...")

        return result.final_output_as(IdeaCritiqueReport)

    async def plan_product(
        self,
        query: str,
        market_report: MarketResearchReport,
        critique_report: IdeaCritiqueReport,
    ) -> Schedule:
        """Plan the product development schedule based on market research and idea critique."""

        print("Starting product development planning...")
        result = await Runner.run(
            self.product_manager_agent.agent_instance,
            f"Product Idea: {query}\n\nMarket Research Report:\n{market_report}\n\nIdea Critique Report:\n{critique_report}",
        )

        print("Product development plan created:")

        return result.final_output_as(Schedule)
