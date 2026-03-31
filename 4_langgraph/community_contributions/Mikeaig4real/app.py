"""Gradio app for Job Hunter AI."""

import gradio as gr
from agent import JobHunterAgent

async def setup_agent():
    """Manage agent instance via Gradio State (official pattern)."""
    agent = JobHunterAgent()
    await agent.setup()
    return agent

def cleanup_agent(agent):
    if agent:
        agent.cleanup()

with gr.Blocks(
    title="Job Hunter AI", 
    theme=gr.themes.Soft(primary_hue="emerald"),
    fill_height=True,
    css=".gradio-container { height: 100vh !important; }"
) as demo:
    # State managed agent
    agent_state = gr.State(delete_callback=cleanup_agent)
    
    gr.Markdown("# Job Hunter AI")
    gr.Markdown("I can find matching jobs for you based on your resume. Just paste a Google Docs link in the chat to get started!")
    
    async def predict(message, history, agent):
        if agent is None:
            agent = await setup_agent()
        
        async for chunk in agent.run(message):
            yield chunk

    chat = gr.ChatInterface(
        fn=predict,
        type="messages",
        fill_height=True,
        additional_inputs=[agent_state]
    )
    
    demo.load(setup_agent, outputs=[agent_state])

if __name__ == "__main__":
    demo.launch(inbrowser=True)
