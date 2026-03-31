import asyncio
from agents import trace, gen_trace_id
from search_planner import PlannerAgent, WebSearchPlan
from search_agent import SearchAgent
from writer_agent import WriterAgent, ReportData
from email_agent import EmailAgent
from clarifier_agent import ClarificationAnswer, ClarifierAgent

RECIPIENT = 'mostafa.kashwaa@hotmail.com'


class ResearchManager:
    def __init__(self):
        self.clarification_agent = ClarifierAgent()
        self.planner_agent = PlannerAgent()
        self.search_agent = SearchAgent()
        self.writer_agent = WriterAgent()
        self.email_agent = EmailAgent()
        self.trace_id = gen_trace_id()
        self.extra_clarity_rounds = 3

    async def clarify_query(self, query: str) -> ClarificationAnswer:
        with trace('Clarification trace', trace_id=self.trace_id):
            print(
                f'View trace at: http://platform.openai.com/traces/trace?trace_id={self.trace_id}')

            clarity = await self.clarification_agent.run(query)
            return clarity

    async def run_research(self, query: str):
        with trace('Research trace', trace_id=self.trace_id):
            print(
                f'View trace at: http://platform.openai.com/traces/trace?trace_id={self.trace_id}')
            yield {'type': 'status', 'content': 'View trace at: http://platform.openai.com/traces/trace?trace_id={self.trace_id}'}

            # Plan the search strategy based on the clarified query
            yield {'type': 'status', 'content': '📋 Planning research...'}
            search_plan: WebSearchPlan = await self.planner_agent.run(query)

            yield {'type': 'status', 'content': f'🌐 Searching web...'}
            search_results = await self._perform_searches(search_plan)

            yield {'type': 'status', 'content': '🧠 Analyzing results and writing report...'}
            report: ReportData = await self.writer_agent.run(search_results)

            yield {'type': 'status', 'content': '📧 Sending email...'}
            await self.email_agent.run(report.markdown_report, RECIPIENT)

            yield {'type': 'status', 'content': '✅ Research complete! Report sent to {RECIPIENT}.'}

            yield {'type': 'result', 'content': report.markdown_report}

    async def _perform_searches(self, search_plan: WebSearchPlan):
        tasks = [asyncio.create_task(self.search_agent.run(
            item)) for item in search_plan.searches]
        results = await asyncio.gather(*tasks)
        return f'Original Query:{search_plan.query}\n\nSummarized Search Results:{results}'
