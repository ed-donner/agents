import gradio as gr
from dotenv import load_dotenv
import phoenix as px

# Tavily + SendGrid tools run inside one MCP subprocess (research_mcp_server.py).
# Run from this folder: uv sync && uv run python deep_research.py
# Keys: TAVILY_API_KEY, SENDGRID_API_KEY; optional SENDGRID_FROM_EMAIL, SENDGRID_TO_EMAIL in .env.
from phoenix.otel import register
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from agents import set_tracing_disabled
from research_manager import ResearchManager

load_dotenv(override=True)

# Initialize Phoenix for local tracing and visualization
session = px.active_session() or px.launch_app()
set_tracing_disabled(True)
tracer_provider = register(project_name="deep_research", auto_instrument=True)
OpenAIAgentsInstrumentor().instrument(tracer_provider=tracer_provider)
print(f"Phoenix UI: {session.url}")


async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)

