import gradio as gr
from ccordinator_agent import CoordinatorAgent
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent

from agents import Runner

load_dotenv(override=True)

async def run(query: str):
    coordinator_agent = CoordinatorAgent().get_agent()
    result = Runner.run_streamed(coordinator_agent, input=query)
    response = ""
    status = ""
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent) and event.data.delta:
            response += event.data.delta
            yield response, status
        elif event.type == "run_item_stream_event":
            item = event.item
            item_type = getattr(item, "type", "")

            if item_type == "tool_call_item":
                tool_name = getattr(item.raw_item, 'name', '')
                log_msg = f"Tool call: {tool_name}\n"
                status += log_msg
                yield response, status

with gr.Blocks(theme=gr.themes.Soft(primary_hue="lime")) as ui:
    gr.Markdown("# Course Instructor Agent")
    query_textbox = gr.Textbox(label="What topic would you like to create a course about?", placeholder="e.g. 'How to learn Python in 3 weeks'")
    run_button = gr.Button("Run", variant="primary")
    logs = gr.Textbox(label="Logs", placeholder="Logs will appear here")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=[report, logs])
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=[report, logs])

ui.launch(inbrowser=True)
