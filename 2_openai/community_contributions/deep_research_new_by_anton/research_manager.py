from agents import (
    Runner,
    RunHooks,
    gen_trace_id,
    trace,
)
from deep_research_agent import research_agent


class StatusHooks(RunHooks):
    async def on_tool_start(self, context, agent, tool):
        print(f"[start] {tool.name}")

    async def on_tool_end(self, context, agent, tool, result):
        print(f"[end]   {tool.name}")


class ResearchManager:

    async def run(self, query: str):
        """Run the deep research process, yielding the status updates and the final report"""
        trace_id = gen_trace_id()

        yield f"Starting research for query: {query}"
        with trace("Research trace", trace_id=trace_id):
            response = Runner.run_streamed(research_agent, query, hooks=StatusHooks())
            async for event in response.stream_events():
                if event.type == "run_item_stream_event":
                    if event.name == "tool_called":
                        tool_name = event.item.tool_name or "unknown_tool"
                        yield f"Tool called: {tool_name}\n"

            final_output = response.final_output
            report = final_output.report
            yield report.markdown_report
