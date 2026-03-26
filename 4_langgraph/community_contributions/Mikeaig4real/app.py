"""Gradio app for Job Hunter AI."""

import gradio as gr
from agent import JobHunterAgent

# agent instance for the session
_agent = None

async def get_agent():
    global _agent
    if _agent is None:
        _agent = JobHunterAgent()
        await _agent.setup()
    return _agent



def cleanup():
    global _agent
    if _agent:
        _agent.cleanup()


with gr.Blocks(
    title="Job Hunter AI", 
    theme=gr.themes.Soft(primary_hue="emerald"),
    fill_height=True,
    css=".gradio-container { height: 100vh !important; }"
) as demo:
    gr.Markdown("# Job Hunter AI")
    gr.Markdown("I can find matching jobs for you based on your resume. Just paste a Google Docs link in the chat to get started!")
    
    async def predict(message, history):
        agent = await get_agent()
        async for chunk in agent.run(message):
            yield chunk

    chat = gr.ChatInterface(
        fn=predict,
        type="messages",
        fill_height=True,
    )

if __name__ == "__main__":
    try:
        demo.launch(inbrowser=True)
    finally:
        cleanup()
