import asyncio

from agents import Agent, ModelSettings, Runner, gen_trace_id, trace

from classifying_ques import ClassifyingQuestions, classifier_agent
from email_agent import email_agent
from planner_agent import WebSearchItem, WebSearchPlan, planner_agent
from search_agent import search_agent
from writer_agent import ReportData, writer_agent


# --- Manager as Agent (agents-as-tools + handoffs) ---
classifier_tool = classifier_agent.as_tool(
    tool_name="classifier",
    tool_description="Generate exactly 3 classifying questions to scope a research query",
)

search_planner_tool = planner_agent.as_tool(
    tool_name="search_planner",
    tool_description="Generate a web-search plan (list of search queries + reasons)",
)

searcher_tool = search_agent.as_tool(
    tool_name="searcher",
    tool_description="Perform a web search and return a concise summary",
)

writer_tool = writer_agent.as_tool(
    tool_name="writer",
    tool_description="Write a detailed markdown report from summarized search results",
)

MANAGER_INSTRUCTIONS = """
You are a research manager coordinating a multi-step research workflow.
You MUST use the provided tools (agents-as-tools) and the provided handoff agent.
Do not answer from your own knowledge.

Workflow:
1) If the input does not already include 3 classifying questions, call the classifier tool to generate them.
2) Call the search_planner tool with the original query AND the classifying questions to tune the plan.
3) For EACH planned search item, call the searcher tool using this exact format:
   Search term: <query>
   Reason for searching: <reason>
4) Call the writer tool with:
   Original query: <original query>
   Summarized search results: <list of summaries>
5) Handoff to the Email agent with the final markdown report so it sends exactly ONE email.

Output rules:
- Your final output must be ONLY the markdown report (no preamble, no tool traces).
"""

manager_agent = Agent(
    name="ResearchManager",
    instructions=MANAGER_INSTRUCTIONS,
    tools=[classifier_tool, search_planner_tool, searcher_tool, writer_tool],
    handoffs=[email_agent],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"),
)

class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("Starting research...")

            yield "Generating 3 classifying questions..."
            cq_result = await Runner.run(classifier_agent, input=f"Query: {query}")
            cq = cq_result.final_output_as(ClassifyingQuestions)

            if cq.questions:
                yield "Classifying questions:\n" + "\n".join(
                    f"{i+1}. {q}" for i, q in enumerate(cq.questions[:3])
                )

            yield "Running manager agent (tools + handoff)..."
            manager_input = (
                f"Query: {query}\n"
                "Classifying questions:\n"
                + "\n".join(f"- {q}" for q in (cq.questions or [])[:3])
            )
            result = await Runner.run(manager_agent, input=manager_input)

            yield "Research complete"
            classifying_block = ""
            if cq.questions:
                classifying_block = (
                    "## Classifying questions\n"
                    + "\n".join(f"{i+1}. {q}" for i, q in enumerate(cq.questions[:3]))
                    + "\n\n---\n\n"
                )

            yield classifying_block + str(result.final_output)
        

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> list[str]:
        """ Perform the searches to perform for the query """
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
        """ Perform a search for the query """
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
        """ Write the report for the query """
        print("Thinking about report...")
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        result = await Runner.run(
            writer_agent,
            input,
        )

        print("Finished writing report")
        return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        print("Writing email...")
        result = await Runner.run(
            email_agent,
            report.markdown_report,
        )
        print("Email sent")
        return report
