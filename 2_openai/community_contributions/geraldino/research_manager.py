import asyncio
from agents import Runner, trace, gen_trace_id
from my_agents import (
    query_refiner_agent, planner_agent, validator_agent,
    search_agent, writer_agent, evaluator_agent, email_agent,
    WebSearchItem, WebSearchPlan, RefinedQuery,
    ReportData, EvaluationResult, ValidationResult,
)

# Research Manager: This class is responsible for orchestrating the deep research process.
class ResearchManager:

    async def run(self, query: str):
        """Run the enhanced deep research process, yielding status updates and the final report."""
        trace_id = gen_trace_id()
        with trace("Enhanced Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n\n"

            # Step 1: Refine the raw query
            yield "**Step 1: Refining your query...**\n\n"
            refined = await self.refine_query(query)
            yield f"- Original: *{refined.original_query}*\n"
            yield f"- Refined: *{refined.refined_query}*\n\n"

            # Step 2: Plan and validate searches autonomously
            yield "**Step 2: Planning and validating searches...**\n\n"
            search_plan = await self.plan_searches_with_validation(refined.refined_query, max_attempts=3)
            queries_display = "\n".join([f"- {item.query}" for item in search_plan.searches])
            yield f"Approved search queries:\n{queries_display}\n\n"

            # Step 3: Perform searches in parallel
            yield "**Step 3: Searching the web...**\n\n"
            search_results = await self.perform_searches(search_plan)
            yield "Searches complete.\n\n"

            # Step 4: Write the report
            yield "**Step 4: Writing report...**\n\n"
            report = await self.write_report(refined.refined_query, search_results)
            yield "Report written.\n\n"

          # Step 5: Evaluate research quality
            yield "**Step 5: Evaluating research quality...**\n\n"
            evaluation = await self.evaluate_research(refined.refined_query, search_plan, search_results)
            scorecard = self.format_scorecard(evaluation)
            yield "Evaluation complete.\n\n"      

            # Step 6: Send email with scorecard
            yield "**Step 6: Sending email...**\n\n"
            await self.send_email(report, scorecard)  
            yield "Email sent!\n\n"

            # Final: yield full report, then scorecard below as appendix
            yield report.markdown_report + "\n\n---\n\n" + scorecard

    # ── Step methods 
    # Refine Query: This method is responsible for refining the user's query into a more specific and focused research question.

    async def refine_query(self, query: str) -> RefinedQuery:
        """Use the query refiner agent to improve the raw user query."""
        print("Refining query...")
        result = await Runner.run(query_refiner_agent, query)
        print(f"Refined: {result.final_output.refined_query}")
        return result.final_output_as(RefinedQuery)

    # Plan Searches with Validation: This method is responsible for planning the web searches needed to answer the research question and validating them.
    async def plan_searches_with_validation(self, refined_query: str, max_attempts: int = 3) -> WebSearchPlan:
        """Autonomously plan and validate searches, rerunning until queries are sufficient."""
        all_attempts: list[WebSearchPlan] = []
        current_query = refined_query

        for attempt in range(1, max_attempts + 1):
            print(f"Planning searches (attempt {attempt}/{max_attempts})...")

            # Run the planner agent to plan the web searches
            planner_result = await Runner.run(planner_agent, f"Query: {current_query}")
            current_plan = planner_result.final_output_as(WebSearchPlan)
            all_attempts.append(current_plan)
            print(f"Generated {len(current_plan.searches)} queries. Validating...")

            # Run the validator agent to validate the web searches
            validation_input = (
                f"Refined research question: {refined_query}\n\n"
                f"Proposed search queries:\n"
                + "\n".join([f"- {item.query} (reason: {item.reason})" for item in current_plan.searches])
            )
            validation_result = await Runner.run(validator_agent, validation_input)
            validation = validation_result.final_output_as(ValidationResult)

            print(f"Validation: {'✅ Sufficient' if validation.is_sufficient else '❌ Insufficient'}")
            print(f"Reasoning: {validation.reasoning}")

            if validation.is_sufficient:
                print(f"Accepted on attempt {attempt}.")
                return current_plan

            # Feed gaps back into next planning attempt
            if validation.gaps:
                print(f"Gaps found: {validation.gaps}")
                current_query = (
                    f"{refined_query}\n\n"
                    f"Make sure to cover these missing angles: {', '.join(validation.gaps)}"
                )

        # Fallback to last attempt — most refined due to gap feedback
        print(f"Max attempts reached. Using best available plan from attempt {len(all_attempts)}.")
        return all_attempts[-1]

    # Perform Searches: This method is responsible for performing the web searches in parallel.
    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """Perform all searches in parallel."""
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

    # Search: This method is responsible for performing a single web search using the search agent.
    async def search(self, item: WebSearchItem) -> str | None:
        """Run a single web search using the search agent."""
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(search_agent, input)
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed for '{item.query}': {e}")
            return None

    # Write Report: This method is responsible for writing a report based on the search results.
    async def write_report(self, query: str, search_results: list[str]) -> ReportData:
        """Use the writer agent to synthesize search results into a full report."""
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(writer_agent, input)
        print("Finished writing report")
        return result.final_output_as(ReportData)

    # Evaluate Research: This method is responsible for evaluating the quality of the research report.
    async def evaluate_research(self, refined_query: str, search_plan: WebSearchPlan, search_results: list[str]) -> EvaluationResult:
        """Use the evaluator agent to score the research quality 1-10."""
        print("Evaluating research quality...")
        queries_section = "\n".join([
            f"Query {i+1}: {item.query}\n  Reason: {item.reason}"
            for i, item in enumerate(search_plan.searches)
        ])
        results_section = "\n\n".join([
            f"Result {i+1} (for '{search_plan.searches[i].query}'):\n{result}"
            for i, result in enumerate(search_results)
        ])
        evaluation_input = (
            f"Refined Research Question: {refined_query}\n\n"
            f"=== SEARCH QUERIES USED ===\n{queries_section}\n\n"
            f"=== SEARCH RESULT SUMMARIES ===\n{results_section}"
        )
        result = await Runner.run(evaluator_agent, evaluation_input)
        print("Evaluation complete")
        return result.final_output_as(EvaluationResult)

    # Send Email: This method is responsible for sending the research report via email.
    async def send_email(self, report: ReportData, scorecard: str) -> None:
        """Use the email agent to format and send the report with scorecard as appendix."""
        print("Writing email...")
        email_content = (
        report.markdown_report
        + "\n\n---\n\n"
        + "## 📎 Appendix: Research Quality Evaluation\n\n"
        + scorecard
        )
        await Runner.run(email_agent, email_content)
        print("Email sent")

    # Format Scorecard: This method is responsible for formatting the evaluation result as a markdown scorecard string.
    def format_scorecard(self, evaluation: EvaluationResult) -> str:
        """Format the evaluation result as a markdown scorecard string."""
        return (
            f"## 📊 Research Quality Scorecard: {evaluation.score}/10\n\n"
            f"**Verdict:** {evaluation.verdict}\n\n"
            f"**Coverage:** {evaluation.coverage_assessment}\n\n"
            f"**Quality:** {evaluation.quality_assessment}\n\n"
            f"**Alignment:** {evaluation.alignment_assessment}\n\n"
            f"**Strengths:** {', '.join(evaluation.strengths)}\n\n"
            f"**Weaknesses:** {', '.join(evaluation.weaknesses)}\n\n"
            "---\n\n"
        )
