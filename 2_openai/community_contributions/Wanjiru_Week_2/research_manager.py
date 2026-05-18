import asyncio
from agents import Runner

from agents_config import planner, search_agent, writer, evaluator, clarifier, refiner


MAX_ITERATIONS = 3


class ResearchManager:

    async def run(self, query: str, answers: str = ""):
        clarifier_result = await Runner.run(clarifier, query)
        questions = clarifier_result.final_output.questions if hasattr(clarifier_result.final_output, "questions") else []

        if questions and not answers:
            yield "### Clarifying questions:\n" + "\n".join(f"- {q}" for q in questions)
            return

        if answers:
            query = f"{query}\nUser clarifications:\n{answers}"

        current_query = query
        final_report = ""

        for i in range(MAX_ITERATIONS):
            yield f"\n--- Iteration {i+1} ---\n"

            plan_result = await Runner.run(planner, current_query)
            searches = plan_result.final_output.searches

            tasks = [
                Runner.run(search_agent, f"Search: {item.query}\nReason: {item.reason}")
                for item in searches
            ]

            results = await asyncio.gather(*tasks)

            summaries = []
            for r in results:
                if r and r.final_output:
                    summaries.append(str(r.final_output))

            writer_input = f"""
            Query: {current_query}

            Search results:
            {summaries}
            """

            report_result = await Runner.run(writer, writer_input)

            report = report_result.final_output

            if hasattr(report, "content"):
                report_text = report.content
            elif hasattr(report, "markdown_report"):
                report_text = report.markdown_report
            else:
                report_text = str(report)

            final_report = report_text

            eval_result = await Runner.run(evaluator, report_text)
            eval_output = eval_result.final_output

            is_good = getattr(eval_output, "is_sufficient", False)
            feedback = getattr(eval_output, "feedback", str(eval_output))

            if is_good:
                yield "✅ Report is sufficient."
                yield report_text
                return

            yield "🔁 Refining research..."

            refine_input = f"""
            Query: {current_query}

            Feedback:
            {feedback}
            """

            refined = await Runner.run(refiner, refine_input)
            current_query = str(refined.final_output)

        yield "⚠️ Max iterations reached. Final report:"
        yield final_report