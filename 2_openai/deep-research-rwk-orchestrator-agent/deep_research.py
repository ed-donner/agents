"""  point of entry for the deep research project 
    gradio interface to run the deep research project
    takes a query and yields the progress and the final report

    calls run which calls ResearchManager().run(query) -- the research_manager, which:
        calls plan_searches which calls planner_agent to produce WebSearchPlan
        calls perform_searches which calls search_agent to produce SearchResults
        calls filter_results which calls filter_agent to produce FilteredResults
        calls write_report which calls writer_agent to produce ReportData
        call review_report which calls review_agent to produce ReviewResult
            if review_agent finds the report not acceptable, call write_report again
        calls publish_email which calls publish_report to produce an html report file

 """

import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    # format gradio page
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)

