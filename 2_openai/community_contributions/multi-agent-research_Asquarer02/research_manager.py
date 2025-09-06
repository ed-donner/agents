from agents import Agent, Runner, trace, gen_trace_id
from search_agent import search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from clarify_agent import clarify_agent, ClarificationQuestions
import asyncio

class ResearchManager:
    def __init__(self):
        # Create the research manager agent with other agents as tools
        self.manager_agent = Agent(
            name="ResearchManager",
            instructions=(
                "You are a research manager coordinating a team of specialized agents to conduct thorough research.\n"
                "Your process is:\n"
                "1. First use the clarify_agent to generate clarifying questions\n"
                "2. After getting answers, use the planner_agent to create a search strategy\n"
                "3. Coordinate the search_agent to gather information\n"
                "4. Finally, use the writer_agent to create a comprehensive report\n\n"
                "You should ensure each step builds on the previous one and maintains focus on the original query."
            ),
            tools=[
                clarify_agent.as_tool(
                    tool_name="clarify",
                    tool_description="Generate clarifying questions for the research query"
                ),
                planner_agent.as_tool(
                    tool_name="plan",
                    tool_description="Create a search strategy based on the query and clarifications"
                ),
                search_agent.as_tool(
                    tool_name="search",
                    tool_description="Perform web searches to gather information"
                ),
                writer_agent.as_tool(
                    tool_name="write",
                    tool_description="Generate a comprehensive research report"
                )
            ],
            model="gpt-4o-mini"
        )

    async def run(self, query: str, clarification_answers: str = None):
        """Run the enhanced research process with clarifying questions"""
        trace_id = gen_trace_id()
        with trace("Enhanced Research Process", trace_id=trace_id):
            # yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # Step 1: Generate clarifying questions
            yield "Generating clarifying questions..."
            clarification_result = await Runner.run(
                clarify_agent,  # Use the agent directly instead of through the manager
                f"Original query: {query}"
            )
            clarifications = clarification_result.final_output_as(ClarificationQuestions)
            yield f"Clarifying questions:\n" + "\n".join(f"- {q}" for q in clarifications.questions)
            yield f"\nReasoning: {clarifications.reasoning}"
            
            # Step 2: Get answers to clarifying questions
            if clarification_answers is None:
                yield "Please provide answers to the clarifying questions..."
                return
            
            # Step 3: Create search plan
            yield "Creating search strategy..."
            plan_result = await Runner.run(
                planner_agent,  # Use the agent directly
                f"Original query: {query}\n\n"
                f"Clarifying questions and answers:\n{clarification_answers}\n\n"
            )
            search_plan = plan_result.final_output_as(WebSearchPlan)
            yield f"Search strategy created: {search_plan.overall_strategy}"
            
            # Step 4: Perform searches
            yield "Performing searches..."
            search_results = []
            for search_item in search_plan.searches:
                search_result = await Runner.run(
                    search_agent,  # Use the agent directly
                    f"Search query: {search_item.query}\n"
                    f"Reason: {search_item.reason}\n"
                    f"Expected focus: {search_item.expected_focus}"
                )
                if search_result is not None:
                    search_results.append(str(search_result.final_output))
            
            # Step 5: Generate report
            yield "Generating comprehensive report..."
            report_result = await Runner.run(
                writer_agent,  # Use the agent directly
                f"Original query: {query}\n\n"
                f"Clarifying questions and answers:\n{clarification_answers}\n\n"
                f"Search results:\n" + "\n".join(search_results)
            )
            report = report_result.final_output_as(ReportData)
            
            yield "Research complete!"
            yield report.markdown_report 