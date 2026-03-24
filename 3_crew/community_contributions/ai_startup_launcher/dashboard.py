import gradio as gr
import asyncio
from crew import AIStartupLauncher

launcher = AIStartupLauncher().crew()

async def run_idea(idea):
    result = await asyncio.to_thread(
        launcher.kickoff,
        inputs={"idea": idea}
    )
    return result

iface = gr.Interface(
    fn=lambda idea: asyncio.run(run_idea(idea)),
    inputs=gr.Textbox(label="Startup Idea"),
    outputs=gr.Textbox(label="Result"),
    title="AI Startup Launcher"
)

iface.launch()