from agents import Runner
from agency import orchestrator_agent
import gradio as gr
import asyncio

async def run(query: str):
    result = await Runner.run(orchestrator_agent, query)
    return result.final_output

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Code Review and Refactor")
    query_textbox = gr.Textbox(label="What is the code you want to review and refactor?", placeholder="Type or paste the repository URL or local directory path")
    review_btn = gr.Button("Review and Refactor", variant="primary")
    report = gr.Markdown(label="Report")

    review_btn.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)

if __name__ == "__main__":
    asyncio.run(run("https://github.com/openai/openai-cookbook"))