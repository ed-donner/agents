from agents import Runner, trace, gen_trace_id
from medical_paper_search_agent import medical_search_agent
from medical_paper_planner_agent import medical_planner_agent, MedicalSearchItem, MedicalSearchPlan
from medical_report_writer_agent import medical_writer_agent, MedicalReportData
from medical_guardrail_agent import medical_guardrail_agent, GuardrailDecision
from email_agent import email_agent
import asyncio

class MedicalResearchManager:

    async def run(self, query: str, email: str = None):
        """Run the medical deep research process, yielding status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Medical Research Trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"🔬 **Medical Research Trace**\n\nView trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n\n"
            
            # Guardrail check
            yield "🛡️ **Checking query relevance...**\n\n"
            guardrail_result = await self.check_guardrail(query)
            if not guardrail_result.is_medical:
                error_msg = (
                    f"❌ **Query Not Medical/Health-Related**\n\n"
                    f"**Reason:** {guardrail_result.reasoning}\n\n"
                    f"This tool is designed specifically for medical, health, and clinical research topics.\n\n"
                )
                if guardrail_result.suggested_redirect:
                    error_msg += f"**Suggestion:** This query might be better suited for a {guardrail_result.suggested_redirect} research tool.\n\n"
                error_msg += "Please provide a medical, health, or clinical research query.\n\n"
                error_msg += "**Examples of acceptable queries:**\n"
                error_msg += "- 'Efficacy of mRNA vaccines in preventing severe COVID-19 outcomes'\n"
                error_msg += "- 'Latest treatment protocols for type 2 diabetes'\n"
                error_msg += "- 'Impact of sleep deprivation on cognitive function'\n"
                error_msg += "- 'Comparative effectiveness of antidepressants in major depressive disorder'\n"
                yield error_msg
                return
            
            yield "✅ **Query approved for medical research**\n\n"
            yield "📋 **Planning medical literature search strategy...**\n\n"
            search_plan = await self.plan_searches(query)
            yield f"✅ **Search plan complete** - Will search for {len(search_plan.searches)} medical/academic topics\n\n"
            yield "🔍 **Searching medical databases and academic journals...**\n\n"
            search_results = await self.perform_searches(search_plan)
            yield f"✅ **Literature search complete** - Found {len(search_results)} sets of relevant papers\n\n"
            yield "✍️ **Writing comprehensive medical literature review...**\n\n"
            report = await self.write_report(query, search_results)
            yield "✅ **Medical report written**\n\n"
            if email:
                yield "📧 **Sending report via email...**\n\n"
                await self.send_email(report, email)
                yield "✅ **Email sent successfully**\n\n"
            yield "---\n\n"
            yield report.markdown_report
        

    async def check_guardrail(self, query: str) -> GuardrailDecision:
        """Check if the query is medical/health-related"""
        print("Checking guardrail...")
        result = await Runner.run(
            medical_guardrail_agent,
            f"User query: {query}",
        )
        return result.final_output_as(GuardrailDecision)

    async def plan_searches(self, query: str) -> MedicalSearchPlan:
        """Plan the medical/academic searches to perform for the query"""
        print("Planning medical searches...")
        result = await Runner.run(
            medical_planner_agent,
            f"Medical query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} medical searches")
        return result.final_output_as(MedicalSearchPlan)

    async def perform_searches(self, search_plan: MedicalSearchPlan) -> list[str]:
        """Perform the medical/academic searches"""
        print("Searching medical databases...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search_papers(item)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching medical databases")
        return results

    async def search_papers(self, item: MedicalSearchItem) -> str | None:
        """Perform a medical/academic paper search"""
        input_text = f"Medical search term: {item.query}\nReason for searching: {item.reason}"
        try:
            result = await Runner.run(
                medical_search_agent,
                input_text,
            )
            return str(result.final_output)
        except Exception as e:
            print(f"Search failed: {e}")
            return None

    async def write_report(self, query: str, search_results: list[str]) -> MedicalReportData:
        """Write the medical literature review report"""
        print("Writing medical report...")
        input_text = f"Original medical query: {query}\n\nSummarized research findings from academic papers:\n\n" + "\n\n".join(search_results)
        result = await Runner.run(
            medical_writer_agent,
            input_text,
        )
        print("Finished writing medical report")
        return result.final_output_as(MedicalReportData)
    
    async def send_email(self, report: MedicalReportData, email: str = None) -> None:
        print("Sending medical report via email...")
        # EmailJS requires email parameter, so we pass it along with the report
        email_input = f"Medical Research Report:\n\n{report.markdown_report}\n\nRecipient email: {email if email else 'None'}"
        result = await Runner.run(
            email_agent,
            email_input,
        )
        print("Email sent")
        return report

