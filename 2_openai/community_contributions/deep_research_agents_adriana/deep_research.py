import gradio as gr
import asyncio
from agents import Runner, trace, gen_trace_id
from manager_agent import manager_agent, EmailOut


async def run(query: str):
    """Show only the trace link, a start status, then the final report."""
    trace_id = gen_trace_id()
    link = f'https://platform.openai.com/traces/trace?trace_id={trace_id}'
    trace_md = f"[View trace]({link})"

    yield trace_md, ""

    yield f"{trace_md}\n\nStarting research…", ""

    with trace("Research trace", trace_id=trace_id):
        result = await Runner.run(manager_agent, f"User query: {query}")

    report_md = ""
    try:
        email_out = result.final_output_as(EmailOut)
        report_md = (email_out.markdown_report or "").strip()
    except Exception:
        
        raw = getattr(result, "final_output", result)
        if isinstance(raw, dict):
            report_md = raw.get("markdown_report") or raw.get("report_markdown") or str(raw)
        else:
            report_md = str(raw)

    yield f"{trace_md}\n\nDone ✅", report_md



with gr.Blocks(theme = gr.themes.Default(primary_hue = 'sky')) as ui:
    gr.Markdown(' Deep Research Agent Project')
    query_textbox = gr.Textbox(label = 'What topic would you like to research',
    placeholder = 'e.g, latest News about GenAI',
    lines = 8,
    max_lines = 20,
    scale = 2)

    run_button = gr.Button('Start Research', variant = 'primary')
    status = gr.Markdown(label = 'Status')
    report = gr.Markdown(label = 'Research Report')

    run_button.click(fn = run, inputs = query_textbox, outputs = [status, report])
    query_textbox.submit(fn = run, inputs = query_textbox, outputs = [status, report])

ui.launch(inbrowser = True)