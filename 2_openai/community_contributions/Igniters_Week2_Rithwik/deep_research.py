import gradio as gr
from dotenv import load_dotenv
from agents import Runner, trace, gen_trace_id
from openai.types.responses import ResponseTextDeltaEvent
from research_agent import research_agent
from planner_agent import WebSearchPlan
from writer_agent import ReportData

load_dotenv(override=True)


async def run(query: str):
    """Run the agentic research pipeline, streaming status updates and the final report."""
    trace_id = gen_trace_id()
    status_lines = []
    final_report = ""

    def current_display():
        display = "\n\n".join(status_lines)
        if final_report:
            display += f"\n\n---\n\n{final_report}"
        return display

    tracer = trace("Research trace", trace_id=trace_id)
    tracer.__enter__()

    try:
        status_lines.append(f"🔗 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
        status_lines.append("🚀 Starting research...")
        yield current_display()

        result = Runner.run_streamed(research_agent, query)

        async for event in result.stream_events():

            if event.type == "run_item_stream_event":

                # Tool call item
                if event.item.type == "tool_call_item":
                    tool_name = event.item.raw_item.name
                    status_map = {
                        "plan_searches": "  Planning searches...",
                        "web_search":    " Searching the web...",
                        "write_report":  "  Writing report...",
                        "send_email":    " Sending email...",
                    }
                    status_lines.append(status_map.get(tool_name, f"Calling {tool_name}..."))
                    yield current_display()

                # Tool call output item
                elif event.item.type == "tool_call_output_item":
                    output = event.item.output

                    # Case 1: already a deserialized Pydantic object
                    if isinstance(output, ReportData):
                        final_report = output.markdown_report
                        status_lines.append("Report written")
                        yield current_display()

                    elif isinstance(output, WebSearchPlan):
                        count = len(output.searches)
                        status_lines.append(f"Search plan ready — {count} searches planned")
                        yield current_display()

                    # Case 2: a plain string (web_search result or send_email confirmation)
                    elif isinstance(output, str):
                        if "email" in output.lower() or "sent" in output.lower():
                            status_lines.append("Email sent — research complete!")
                        else:
                            status_lines.append(" Search result received")
                        yield current_display()

                    # Case 3: unexpected type — log it silently for debugging
                    else:
                        status_lines.append(f"Tool result received ({type(output).__name__})")
                        yield current_display()

            # Token (text) streaming
            elif event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    if not final_report:
                        final_report += event.data.delta
                        yield current_display()

    finally:
        tracer.__exit__(None, None, None)


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)