from agents import Runner, trace, gen_trace_id
from orchestrator_agent import orchestrator_agent
from publish_agent import publish_agent, PublishData
from writer_agent import ReportData
from parameters import MAX_ORCH_AGENT_TURNS


# prints and yields, manages & shows progress of the project
class Report_Manager:

    def __init__(self):
        self.report: ReportData | None = None     # set when orchestration completes
        self.report_file_name: str | None = None  # set when publishing completes

    async def run(self, query: str):
        """ Run the deep research process, yield progress lines, publish the final report.
            The final report is available in self.report after the generator finishes.
        """

        trace_id = gen_trace_id()
        with trace("Research trace", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            print("\nStarting research...")
            yield "**Orchestrator agent started.**"

        # run_streamed returns immediately; events arrive while the agent works
        result = Runner.run_streamed(
            orchestrator_agent,
            f"Query: {query}",
            max_turns=MAX_ORCH_AGENT_TURNS
        )

        call_names = {}  # map tool call_id -> tool name, to label the close events
        async for event in result.stream_events():
            if event.type != "run_item_stream_event":
                continue
            item = event.item
            if item.type == "tool_call_item":
                name = getattr(item.raw_item, "name", "unknown tool")
                call_id = getattr(item.raw_item, "call_id", None)
                call_names[call_id] = name
                print(f"Calling tool: {name}")
                yield f"Calling tool `{name}` ..."
            elif item.type == "tool_call_output_item":
                raw = item.raw_item
                call_id = raw.get("call_id") if isinstance(raw, dict) else getattr(raw, "call_id", None)
                name = call_names.get(call_id, "unknown tool")
                print(f"Tool completed: {name}")
                yield f"Tool `{name}` completed."

        self.report = result.final_output_as(ReportData)
        print("Orchestration completed\n")
        yield "**Orchestrator agent completed.**"

        # publish deterministically: always produce the HTML report file
        print("Publishing report...")
        yield "**Publish agent started.**"
        publish_result = await Runner.run(
            publish_agent,
            f"Report: {self.report.model_dump_json()}",
        )
        self.report_file_name = publish_result.final_output_as(PublishData).report_file_name
        print(f"Report published: {self.report_file_name}\n")
        yield f"**Publish agent completed.** Report published to file: `{self.report_file_name}`"
