from agents import Runner, trace, gen_trace_id
# from pydantic import BaseModel, Field
from orchestrator_agent import orchestrator_agent
from writer_agent import ReportData

import asyncio




# prints and yields, manages & shows progress of the project
class ResearchManager:

    async def run(self, query: str):
        """ Run the deep research process, show progress, publish the final report"""

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("\nStarting research...")
            yield "Starting research, initiating orchestration, ..."
        
        
        result = await Runner.run(
            orchestrator_agent,
            f"Query: {query}",
        )
        report = result.final_output.markdown_report
        print("Orchestration completed\n")
        yield "Orchestration completed"
        yield report

       