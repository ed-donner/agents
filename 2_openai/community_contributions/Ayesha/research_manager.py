from agents import Runner
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
import asyncio
import arxiv


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process"""
        print("Starting research...")
        yield "Starting research..."

        search_plan = await self.plan_searches(query)
        yield "Searches planned, starting to search..."

        search_results = await self.perform_searches(search_plan)
        yield "Searches complete, writing report..."

        report = await self.write_report(query, search_results)

        yield "Report written"
        yield report.markdown_report

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Plan the searches to perform"""
        print("Planning searches...")

        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )

        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform searches using arXiv"""
        print("Searching...")

        tasks = [
            asyncio.create_task(self.search(item))
            for item in search_plan.searches
        ]

        results = []
        num_completed = 0

        for task in asyncio.as_completed(tasks):
            result = await task
            if result:
                results.append(result)

            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")

        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        """Search arXiv for real papers"""
        
        try:
            search = arxiv.Search(
                query=item.query,
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )

            papers = []

            for result in search.results():
                papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "year": result.published.year,
                    "summary": result.summary,
                    "url": result.entry_id
                })

            formatted = ""
            for p in papers:
                formatted += f"""
Title: {p['title']}
Authors: {', '.join(p['authors'])}
Year: {p['year']}
URL: {p['url']}
Summary: {p['summary'][:500]}
---
"""

            return formatted.strip()

        except Exception as e:
            print(f"Search failed: {e}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Write final report using REAL data"""
        print("Thinking about report...")

        input = f"""
Original query:
{query}

You are given REAL research paper data below extracted from arXiv.

STRICT RULES:
- Use ONLY the provided papers
- Do NOT invent papers, authors, or citations
- Base your analysis strictly on the summaries

Research Data:
{search_results}
"""

        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)