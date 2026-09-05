from agents import Runner, trace, gen_trace_id
from clarifier_agent import clarifier_agent, ClarifyingQuestions
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from evaluator_agent import evaluator_agent, EvaluationResult
from email_agent import email_agent
import asyncio

MAX_REFINEMENTS = 2  # extra search rounds if the evaluator is not satisfied


class ResearchManager:

    async def clarify(self, query: str) -> list[str]:
        """ Challenge #1: ask a few clarifying questions before researching """
        print("Asking clarifying questions...")
        result = await Runner.run(clarifier_agent, f"Query: {query}")
        return result.final_output_as(ClarifyingQuestions).questions

    # ---- pure input builders: keep clarifications flowing through every stage (offline-testable) ----

    @staticmethod
    def format_clarifications(questions: list[str], answers: list[str]) -> str:
        """ Combine the clarifying questions and the user's answers into a context block.
        Returns an empty string when there are no clarifications. """
        pairs = [(q, a) for q, a in zip(questions, answers) if q]
        if not pairs:
            return ""
        lines = [f"- Q: {q}\n  A: {a}" for q, a in pairs]
        return "Clarifications provided by the user:\n" + "\n".join(lines)

    @staticmethod
    def build_planner_input(query: str, clarifications: str = "", feedback: str = "") -> str:
        parts = [f"Query: {query}"]
        if clarifications:
            parts.append(clarifications)
        if feedback:
            parts.append(
                "A previous round of research was judged incomplete. Focus the new searches on "
                f"addressing this feedback:\n{feedback}"
            )
        return "\n\n".join(parts)

    @staticmethod
    def build_search_input(item: WebSearchItem, clarifications: str = "") -> str:
        parts = [f"Search term: {item.query}", f"Reason for searching: {item.reason}"]
        if clarifications:
            parts.append(clarifications + "\nFocus your summary on what these clarifications ask for.")
        return "\n".join(parts)

    @staticmethod
    def build_writer_input(query: str, search_results: list[str], clarifications: str = "") -> str:
        parts = [f"Original query: {query}"]
        if clarifications:
            parts.append(clarifications + "\nMake sure the report directly addresses these clarifications.")
        parts.append(f"Summarized search results: {search_results}")
        return "\n\n".join(parts)

    @staticmethod
    def build_evaluator_input(query: str, clarifications: str, search_results: list[str]) -> str:
        parts = [f"Original query: {query}"]
        if clarifications:
            parts.append(clarifications)
        parts.append(f"Search summaries gathered so far:\n{search_results}")
        return "\n\n".join(parts)

    # ---- orchestration ----

    async def run(self, query: str, questions: list[str] | None = None, answers: list[str] | None = None):
        """ Run the deep research process, yielding status updates and the final report.
        The clarifications are threaded through planning, searching, evaluation and writing. """
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            clarifications = self.format_clarifications(questions or [], answers or [])

            search_plan = await self.plan_searches(query, clarifications)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan, clarifications)

            yield "Searches complete, checking alignment with your clarifications..."
            evaluation = await self.evaluate(query, clarifications, search_results)
            attempt = 0
            while not evaluation.aligned and attempt < MAX_REFINEMENTS:
                attempt += 1
                yield f"Results not fully aligned, refining (round {attempt})..."
                search_plan = await self.plan_searches(query, clarifications, feedback=evaluation.feedback)
                search_results += await self.perform_searches(search_plan, clarifications)
                evaluation = await self.evaluate(query, clarifications, search_results)

            yield ("Alignment confirmed, writing report..." if evaluation.aligned
                   else "Proceeding with best available results, writing report...")
            report = await self.write_report(query, search_results, clarifications)
            yield "Report written, sending email..."
            await self.send_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def plan_searches(self, query: str, clarifications: str = "", feedback: str = "") -> WebSearchPlan:
        """ Plan the searches, honouring the clarifications and any evaluator feedback """
        print("Planning searches...")
        result = await Runner.run(planner_agent, self.build_planner_input(query, clarifications, feedback))
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan, clarifications: str = "") -> list[str]:
        """ Perform the planned searches concurrently """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item, clarifications)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem, clarifications: str = "") -> str | None:
        """ Perform a single web search, focused by the clarifications """
        try:
            result = await Runner.run(search_agent, self.build_search_input(item, clarifications))
            return str(result.final_output)
        except Exception:
            return None

    async def evaluate(self, query: str, clarifications: str, search_results: list[str]) -> EvaluationResult:
        """ Judge whether the search results truly reflect the query and the clarifications """
        print("Evaluating alignment...")
        result = await Runner.run(
            evaluator_agent, self.build_evaluator_input(query, clarifications, search_results)
        )
        return result.final_output_as(EvaluationResult)

    async def write_report(self, query: str, search_results: list[str], clarifications: str = "") -> ReportData:
        """ Write the report from the search results, honouring the clarifications """
        print("Thinking about report...")
        result = await Runner.run(writer_agent, self.build_writer_input(query, search_results, clarifications))
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def send_email(self, report: ReportData) -> ReportData:
        """ Email the report. Failures are swallowed so a missing email setup
        does not abort the run (testing-friendly). """
        print("Writing email...")
        try:
            await Runner.run(email_agent, report.markdown_report)
            print("Email sent")
        except Exception as e:
            print(f"Email step skipped/failed: {e}")
        return report
