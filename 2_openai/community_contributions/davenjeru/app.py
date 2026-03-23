import asyncio
import traceback
import gradio as gr
from dotenv import load_dotenv
from agents import Runner, RunHooks, RunContextWrapper, Agent, Tool, trace, gen_trace_id, InputGuardrailTripwireTriggered
from manager_agent import ManagerAgent
from reporter_agent import CompetitiveReport

load_dotenv(override=True)

class ProgressHook(RunHooks):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    async def on_agent_start(self, context: RunContextWrapper, agent: Agent):
        await self.queue.put(f"**{agent.name}** started...")

    async def on_agent_end(self, context: RunContextWrapper, agent: Agent, output):
        await self.queue.put(f"**{agent.name}** completed.")

    async def on_tool_start(self, context: RunContextWrapper, agent: Agent, tool: Tool):
        await self.queue.put(f"Calling **{tool.name}**...")

    async def on_tool_end(self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str):
        await self.queue.put(f"**{tool.name}** complete.")

    async def on_handoff(self, context: RunContextWrapper, from_agent: Agent, to_agent: Agent):
        await self.queue.put(f"Handing off from **{from_agent.name}** to **{to_agent.name}**...")


async def run(query: str):
    if not query.strip():
        yield {status: "", report: ""}
        return

    trace_id = gen_trace_id()
    status_log = ""

    with trace("Competitive Intel", trace_id=trace_id):
        trace_url = f"https://platform.openai.com/traces/trace?trace_id={trace_id}"
        status_log = f"[View trace]({trace_url})\n\n"
        yield {status: status_log, report: ""}

        queue = asyncio.Queue()
        hook = ProgressHook(queue)

        try:
            task = asyncio.create_task(
                Runner.run(ManagerAgent, query, hooks=hook)
            )

            while not task.done():
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                    status_log += f"- {msg}\n"
                    yield {status: status_log, report: ""}
                except asyncio.TimeoutError:
                    continue

            result = task.result()

            while not queue.empty():
                msg = queue.get_nowait()
                status_log += f"- {msg}\n"

            output = result.final_output_as(CompetitiveReport)
            status_log += "\n**Analysis complete!**"
            yield {status: status_log, report: output.markdown_report}

        except InputGuardrailTripwireTriggered:
            status_log += "\n<span style=\"color: red;\"><b>Invalid input.</b> Please enter a real product or company name.</span>"
            yield {status: status_log, report: ""}

        except Exception as e:
            status_log += f"\n<span style=\"color: red;\"><b>An error occurred</b>. Try again.</span>"
            traceback.print_exc()
            yield {status: status_log, report: ""}


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Competitive Intelligence Analyzer")
    gr.Markdown("Enter a product or company name to analyze its competitive landscape.")

    with gr.Row():
        with gr.Column(scale=3):
            query_input = gr.Textbox(
                label="Product or Company",
                placeholder='e.g. "Notion", "Figma", "Linear"',
            )
            run_btn = gr.Button("Analyze", variant="primary")
        with gr.Column(scale=1):
            status = gr.Markdown(label="Status", value="", show_label=True)

    report = gr.Markdown(label="Report", value="", show_label=True)

    run_btn.click(fn=run, inputs=query_input, outputs=[status, report])
    query_input.submit(fn=run, inputs=query_input, outputs=[status, report])

ui.launch(inbrowser=True)
