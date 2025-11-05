from agents import Runner, trace, gen_trace_id
from query_parser_agent import query_parser_agent, ClinicalQuery
from planner_agent import planner_agent, MedicalSearchItem, MedicalSearchPlan
from pubmed_agent import pubmed_agent
from clinical_trials_agent import clinical_trials_agent
from pharmgkb_agent import pharmgkb_agent
from clinical_writer_agent import clinical_writer_agent, ClinicalReportData
from email_agent import email_agent
from html_report_generator import generate_html_report
import asyncio


class ResearchManager:

    async def run(self, query: str):
        """Run the pharmacogenomic research process, yielding status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Pharmacogenomic Research", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # Parse the clinical query
            print("Parsing clinical query...")
            yield "**Step 1/6**: Parsing clinical query..."
            parsed_query = await self.parse_query(query)
            yield f"Identified: {parsed_query.disease} | Genes: {', '.join(parsed_query.genes)} | Mutations: {', '.join(parsed_query.mutations)}"
            
            # Plan searches
            print("Planning medical database searches...")
            yield "**Step 2/6**: Planning medical database searches..."
            search_plan = await self.plan_searches(parsed_query)
            yield f"✅ Planned {len(search_plan.searches)} searches\n"
            
            # Execute searches
            print("Executing searches...")
            yield "**Step 3/6**: Executing searches..."
            search_results = await self.perform_searches(search_plan)
            yield f"✅ Completed {len(search_results)} searches\n"
            
            # Write clinical report
            print("Generating report...")
            yield "**Step 4/6**: Generating report..."
            report = await self.write_report(parsed_query, search_results)
            yield f"✅ Report generated ({len(report.markdown_report.split())} words)\n\n"
            
            # Generate HTML report
            print("Creating HTML report...")
            yield "**Step 5/6**: Creating HTML report..."
            html_content, html_path = generate_html_report(report.markdown_report, query)
            yield f"✅ HTML report saved: {html_path}\n"
            
            # Send email
            print("Sending report via email...")
            yield "**Step 6/6**: Sending report via email..."
            await self.send_email(report, html_content)
            yield "✅ Email sent successfully\n"
            
            yield "\n## Report\n\n"
            yield report.markdown_report

    async def parse_query(self, query: str) -> ClinicalQuery:
        """Parse the query to extract structured information"""
        print("Parsing query structure...")
        result = await Runner.run(
            query_parser_agent,
            f"Clinical query: {query}",
        )
        parsed = result.final_output_as(ClinicalQuery)
        print(f"Parsed: Disease={parsed.disease}, Genes={parsed.genes}, Mutations={parsed.mutations}")
        return parsed

    async def plan_searches(self, parsed_query: ClinicalQuery) -> MedicalSearchPlan:
        """Plan the searches across medical databases"""
        print("Planning searches...")
        
        # Format the parsed query for the planner
        query_summary = f"""
Disease: {parsed_query.disease}
Genes: {', '.join(parsed_query.genes)}
Mutations: {', '.join(parsed_query.mutations)}
Clinical Context: {parsed_query.clinical_context}
Research Focus: {parsed_query.search_focus}
"""
        
        result = await Runner.run(
            planner_agent,
            f"Parsed  Query:\n{query_summary}",
        )
        plan = result.final_output_as(MedicalSearchPlan)
        print(f"Planned {len(plan.searches)} searches")
        for search in plan.searches:
            print(f"  - {search.database}: {search.query}")
        return plan

    async def perform_searches(self, search_plan: MedicalSearchPlan) -> list[str]:
        """Perform searches across all databases"""
        print("Executing searches...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Progress: {num_completed}/{len(tasks)} completed")
        
        print("All searches completed")
        return results

    async def search(self, item: MedicalSearchItem) -> str | None:
        """Execute a single search based on the database type"""
        try:
            # Route to the appropriate agent based on database
            if item.database == "PubMed":
                agent = pubmed_agent
            elif item.database == "ClinicalTrials":
                agent = clinical_trials_agent
            elif item.database == "PharmGKB":
                agent = pharmgkb_agent
            else:
                print(f"Unknown database: {item.database}")
                return None
            
            input_text = f"Database: {item.database}\nSearch query: {item.query}\nReason: {item.reason}"
            
            result = await Runner.run(agent, input_text)
            return f"[{item.database}] {item.query}\n\n{str(result.final_output)}"
        
        except Exception as e:
            print(f"Search failed for {item.database} - {item.query}: {str(e)}")
            return None

    async def write_report(self, parsed_query: ClinicalQuery, search_results: list[str]) -> ClinicalReportData:
        """Write the  report"""
        print("Generating report...")
        
        # Format the input for the writer
        query_info = f"""
Disease: {parsed_query.disease}
Genes: {', '.join(parsed_query.genes)}
Mutations: {', '.join(parsed_query.mutations)}
Clinical Context: {parsed_query.clinical_context}
Research Focus: {parsed_query.search_focus}
"""
        
        input_text = f"Clinical Query:\n{query_info}\n\n---\n\nResearch Findings:\n\n" + "\n\n---\n\n".join(search_results)
        
        result = await Runner.run(
            clinical_writer_agent,
            input_text,
        )
        
        report = result.final_output_as(ClinicalReportData)
        print("Report completed")
        return report
    
    async def send_email(self, report: ClinicalReportData, html_content: str) -> None:
        """Send the report via email"""
        print("Sending email...")
        
        # Pass the HTML content to the email agent
        result = await Runner.run(
            email_agent,
            f"Subject: Pharmacogenomic Report\n\nHTML Content:\n{html_content}",
        )
        
        print("Email sent")
        return result
