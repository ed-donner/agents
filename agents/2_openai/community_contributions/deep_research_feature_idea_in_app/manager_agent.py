from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from insight_agent import insight_agent, Insight
from feature_agent import feature_agent, FeatureIdea
from product_manager_agent import product_manager_agent, ClarifiedFeature
from dev_agent import dev_agent, DevHandoff
from proposal_agent import proposal_agent, ProposalDocument
import asyncio
from typing import AsyncGenerator

class ManagerAgent:

    async def run(self, query: str) -> AsyncGenerator[str, None]:
        trace_id = gen_trace_id()
        with trace("AI Pipeline Trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            # 1. Plan and execute searches
            yield "Starting search phase..."
            search_plan = await self.plan_searches(query)
            yield f"Executing {len(search_plan.searches)} searches..."
            search_results = await self.perform_searches(search_plan)
            yield "Search complete, extracting insights..."

            # 2. Extract insights
            insights = await self.extract_insights(search_results)
            yield "Insights extracted, generating feature specs..."

            # 3. Feature ideation
            features = await self.generate_features(insights)
            yield "Features generated..."


            # 4. Product planning (incorporating UI design)
            product_plan = await self.plan_product(features)
            yield "Product plan ready, crafting dev roadmap..."

            # 5. Development roadmap
            dev_roadmap = await self.create_dev_roadmap(product_plan)
            yield "Dev roadmap created, drafting CEO proposal..."

            # 6. Final proposal with embedded wireframes
            proposal_md = await self.draft_proposal(dev_roadmap)
            yield "Pipeline complete."

            # 7. Emit the final Markdown
            yield proposal_md

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan structured web searches for the query."""
        result = await Runner.run(planner_agent, f"Query: {query}")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Execute each WebSearchItem in parallel and collect results."""
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            res = await task
            if res:
                results.append(res)
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Perform a single web search and return the output."""
        try:
            result = await Runner.run(search_agent, f"Search term: {item.query}\nReason: {item.reason}")
            return str(result.final_output)
        except Exception:
            return None

    async def extract_insights(self, search_results: list[str]) -> Insight:
        """Summarize and extract key insights from search results."""
        result = await Runner.run(insight_agent, f"Search results: {search_results}")
        return result.final_output_as(Insight)

    async def generate_features(self, insights: Insight) -> FeatureIdea:
        """Generate feature ideas based on extracted insights."""
        result = await Runner.run(feature_agent, f"Insights: {insights}")
        return result.final_output_as(FeatureIdea)


    async def plan_product(
        self,
        features: FeatureIdea
    ) -> ClarifiedFeature: 
        prompt = (
            f"Features:\n{features}\n\n"
            "Produce a clarified feature spec with business rationale and concerns."
        )
        result = await Runner.run(product_manager_agent, prompt)
        return result.final_output_as(ClarifiedFeature)

    async def create_dev_roadmap(self, product_plan: ClarifiedFeature) -> DevHandoff:
        """Translate the product plan into developer-friendly user stories and acceptance criteria."""
        result = await Runner.run(dev_agent, f"Product plan: {product_plan}")
        return result.final_output_as(DevHandoff)

    async def draft_proposal(
        self,
        dev_roadmap: DevHandoff
    ) -> str:
        prompt = (
            f"Development Roadmap:\n{dev_roadmap}\n\n"
            "Write a polished Markdown proposal for executives, as clear as possible with the given information"
        )
        result = await Runner.run(proposal_agent, prompt)
        doc = result.final_output_as(ProposalDocument)
        return doc.markdown
