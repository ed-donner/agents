from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan, build_planner_instructions
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from clarifier_agent import clarifier_agent, ClarifyingQuestions
from query_refiner_agent import query_refiner_agent, RefinedQuery
from evaluator_agent import evaluator_agent, Evaluation, GapItem
import asyncio

MAX_EVAL_ITERATIONS = 1


class ResearchManager:

    async def run_clarify(self, query: str) -> ClarifyingQuestions:
        """Generate clarifying questions for the user's query."""
        print("Generating clarifying questions...")
        result = await Runner.run(
            clarifier_agent,
            f"Query: {query}",
        )
        return result.final_output_as(ClarifyingQuestions)

    async def refine_query(
        self,
        query: str,
        questions: list[str],
        answers: list[str],
    ) -> RefinedQuery:
        """Refine the query using the user's answers to clarifying questions."""
        print("Refining query...")
        qa_pairs = "\n".join(
            f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)
        )
        input_text = f"Original query: {query}\n\nClarifying Q&A:\n{qa_pairs}"
        result = await Runner.run(
            query_refiner_agent,
            input_text,
        )
        return result.final_output_as(RefinedQuery)

    async def run_research(
        self,
        original_query: str,
        questions: list[str] | None = None,
        answers: list[str] | None = None,
    ):
        """Run the full research pipeline with evaluation loop."""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

            key_focus_areas = None
            if questions and answers:
                yield "Refining your query based on your answers..."
                refined = await self.refine_query(original_query, questions, answers)
                research_query = refined.refined_query
                key_focus_areas = refined.key_focus_areas
                yield f"Refined query: {research_query}"
            else:
                research_query = original_query

            print("Starting research...")
            search_plan = await self.plan_searches(research_query, key_focus_areas)
            yield "Searches planned, starting to search..."
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete, writing report..."
            report = await self.write_report(research_query, search_results)

            # --- Evaluate-and-iterate loop ---
            for iteration in range(MAX_EVAL_ITERATIONS + 1):
                yield f"Evaluating report (round {iteration + 1})..."
                evaluation = await self.evaluate_report(
                    research_query, key_focus_areas, search_results, report,
                )
                yield self._format_evaluation_status(evaluation, iteration + 1)

                if evaluation.verdict == "pass" or iteration == MAX_EVAL_ITERATIONS:
                    break

                high_gaps = [g for g in evaluation.gaps if g.severity == "high"]
                if not high_gaps:
                    break

                yield f"Filling {len(high_gaps)} high-severity gap(s)..."
                gap_results = await self.fill_gaps(high_gaps)
                search_results = search_results + gap_results
                yield "Gap searches complete, revising report..."
                report = await self.write_report(research_query, search_results)

            yield "Report finalized, sending email..."
            await self.deliver_report_email(report)
            yield "Email sent, research complete"
            yield report.markdown_report

    async def evaluate_report(
        self,
        query: str,
        key_focus_areas: list[str] | None,
        search_results: list[str],
        report: ReportData,
    ) -> Evaluation:
        """Evaluate the report for gaps and quality."""
        print("Evaluating report...")
        focus_section = ""
        if key_focus_areas:
            focus_section = f"\nKey focus areas:\n" + "\n".join(f"- {a}" for a in key_focus_areas)

        input_text = (
            f"Original query: {query}"
            f"{focus_section}\n\n"
            f"Search results used ({len(search_results)} sources):\n"
            + "\n---\n".join(search_results[:20])
            + f"\n\n--- REPORT ---\n{report.markdown_report}"
        )
        result = await Runner.run(evaluator_agent, input_text)
        evaluation = result.final_output_as(Evaluation)
        print(
            f"Evaluation: overall={evaluation.overall_score}/10, "
            f"verdict={evaluation.verdict}, gaps={len(evaluation.gaps)}"
        )
        return evaluation

    async def fill_gaps(self, gaps: list[GapItem]) -> list[str]:
        """Run targeted searches for identified gaps."""
        print(f"Filling {len(gaps)} gaps...")
        all_queries = []
        for gap in gaps:
            for query in gap.suggested_searches:
                all_queries.append(
                    WebSearchItem(reason=f"Fill gap: {gap.topic}", query=query)
                )

        tasks = [asyncio.create_task(self.search(item)) for item in all_queries]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
        print(f"Gap filling complete: {len(results)} results")
        return results

    def _format_evaluation_status(self, evaluation: Evaluation, round_num: int) -> str:
        """Format a human-readable evaluation summary for the UI."""
        lines = [
            f"**Evaluation (Round {round_num})**",
            f"- Coverage: {evaluation.coverage_score}/10",
            f"- Depth: {evaluation.depth_score}/10",
            f"- Coherence: {evaluation.coherence_score}/10",
            f"- Overall: {evaluation.overall_score}/10",
            f"- Verdict: {evaluation.verdict}",
        ]
        if evaluation.gaps:
            lines.append(f"- Gaps found: {len(evaluation.gaps)}")
            for g in evaluation.gaps:
                lines.append(f"  - [{g.severity}] {g.topic}")
        lines.append(f"\n{evaluation.summary}")
        return "\n".join(lines)

    # --- Existing methods unchanged below ---

    async def plan_searches(
        self,
        query: str,
        key_focus_areas: list[str] | None = None,
    ) -> WebSearchPlan:
        print("Planning searches...")
        agent = planner_agent
        if key_focus_areas:
            agent = agent.clone(
                instructions=build_planner_instructions(key_focus_areas)
            )
        result = await Runner.run(
            agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem) -> str | None:
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                search_agent,
                input,
            )
            return str(result.final_output)
        except Exception:
            return None

    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )
        print("Finished writing report")
        return result.final_output_as(ReportData)

    async def deliver_report_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report
