import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from agents import Runner

load_dotenv(override=True)


async def run(query: str):
    # Initialize the research manager
    manager = ResearchManager()
    
    # Create the researcher agent (builds tools and handoffs)
    manager.create_researcher()
    
    # Run the researcher and stream the results
    result = Runner.run_streamed(manager.researcher, input=query)
    
    full_output = "## 🔍 Deep Research Progress\n\n"
    yield full_output
    
    async for event in result.stream_events():
        # Show when agents switch
        if event.type == "agent_updated_stream_event":
            agent_name = event.new_agent.name
            full_output += f"\n\n**→ {agent_name} is now active**\n\n"
            yield full_output
        
        # Show when tools are called
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                tool_name = event.item.raw_item.name
                # Format tool names nicely
                if "web_search" in tool_name.lower():
                    full_output += f"🔎 Generating web search queries...\n"
                elif "report" in tool_name.lower():
                    full_output += f"📝 Generating research report...\n"
                elif "send_message" in tool_name.lower():
                    full_output += f"📬 Sending notification...\n"
                else:
                    full_output += f"⚙️ Using tool: {tool_name}\n"
                yield full_output
        
        # Show text output
        elif event.type == "text_delta":
            full_output += event.data
            yield full_output


with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    query_textbox = gr.Textbox(label="What topic would you like to research?")
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

ui.launch(inbrowser=True)