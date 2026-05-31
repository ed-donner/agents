from orchestrator import Orchestrator
import gradio as gr
from dotenv import load_dotenv

load_dotenv(override=True)

async def setup():
    orchestrator = Orchestrator()
    await orchestrator.setup()
    return orchestrator

async def chat(message, history, orchestrator):
    if orchestrator is None:
        return "Still setting up, please wait a moment and try again."
    return await orchestrator.run_superstep(message)



DESCRIPTION = """
# 🔍 Code Analyzer

Paste your code or a code diff into the chat and I will:

-  **Find bugs** — identify errors, logic issues and potential runtime problems
-  **Review style** — check for style violations and code quality issues
-  **Generate a report** — summarize all findings in a clear, structured review
"""

with gr.Blocks(title="Code Analyzer") as ui:
    gr.Markdown(DESCRIPTION)
    orchestrator = gr.State()
    ui.load(setup, [], [orchestrator])
    gr.ChatInterface(chat, type="messages", additional_inputs=[orchestrator])

ui.launch(inbrowser=True)