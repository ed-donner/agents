from agents import Agent, Runner, trace, set_tracing_disabled
from main_agent import main_agent
from eval_agent import eval_agent, EvalData
from search_agent import get_search_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from writer_agent import writer_agent, ReportData
from docker_agent import get_docker_agent
from msg_agent import get_msg_agent
import asyncio
from agents.mcp import MCPServerStdio

# Prevent default cloud tracing/pings
# set_tracing_disabled(True)

class ResearchManager:

    async def run(self, query: str):
        params = {"command": "python", "args": ["mcp_server.py"]}
        with trace("mcp-proj"):
            async with MCPServerStdio(name='MyMcpServer', params=params, client_session_timeout_seconds=1200) as mcp_server:
                mcp_tools = await mcp_server.list_tools()
                print('mcp tools:', mcp_tools)

                """ Run the deep research process, yielding the status updates and the final report"""
                print("Starting research...")
                yield "Generating initial report ..."
                report = await self.main_report(query)
                yield "Initial report generated. Evaluating ..."
                eval_accept = await self.eval_report(query, report.text_report)
                if not eval_accept:
                    yield "Evaluated and not accepted, planning searches ..."
                    search_plan = await self.plan_searches(query)
                    yield "Searches planned, searching ..."
                    search_results = await self.perform_searches(search_plan, get_search_agent(mcp_server))
                    yield "Searches complete, writing report ..."
                    report = await self.write_report(query, search_results)

                yield "Report written, timestamping ..."
                datestamp = await self.call_docker(get_docker_agent(mcp_server))
                text_report = report.text_report
                if '202' in datestamp:
                    text_report += ' This report is generated on ' + datestamp + ' .'

                yield "Timestamped, sending msg ..."
                await self.send_msg(query, text_report, get_msg_agent(mcp_server))
                yield "Msg sent, research complete"
                yield text_report


    async def main_report(self, query: str) -> ReportData:
        """ Generate the concise report for given query """
        print("Generating initial report...")
        result = await Runner.run(
            main_agent,
            f"Query: {query}",
        )
        return result.final_output_as(ReportData)

    async def eval_report(self, query: str, report : str) -> bool:
        """ Evaluate given report for the query """
        print("Evaluating first report...")
        result = await Runner.run(
            eval_agent,
            f"Query: {query}, Report: {report}",
        )
        r = result.final_output_as(EvalData)
        return r.accept

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """ Plan the searches to perform for the query """
        print("Planning searches...")
        result = await Runner.run(
            planner_agent,
            f"Query: {query}",
        )
        print(f"Will perform {len(result.final_output.searches)} searches")
        return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan, search_agent: Agent) -> list[str]:
        """ Perform the searches to perform for the query """
        print("Searching...")
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item, search_agent)) for item in search_plan.searches]
        results = []
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            print(f"Searching... {num_completed}/{len(tasks)} completed")
        print("Finished searching")
        return results

    async def search(self, item: WebSearchItem, search_agent: Agent) -> str | None:
        """ Perform a search for the query """
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        print(input)
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
    
    async def send_msg(self, query: str, report: str, msg_agent: Agent) -> str:
        print("Writing msg...")
        result = ''
        try:
            result = await Runner.run(
                msg_agent,
                f"Query: {query}, Report: {report}",
                max_turns=1,  # <= decide+call, then synthesize
            )
        except Exception:
            print('Allowing only 1 send message tool call.')
            pass
        print("Message sent")
        return result

    async def call_docker(self, docker_agent: Agent) -> str:
        print("Applying Timestamp...")
        try:
            result = await Runner.run(docker_agent, "Call docker tool.", max_turns=2)
            print('result:', result)
            return result.final_output_as(str)
        except Exception:
            from dockertool import get_docker_resp
            return get_docker_resp()

