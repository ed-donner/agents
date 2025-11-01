import gradio as gr
from dotenv import load_dotenv
from agents import Runner,trace, gen_trace_id
from clarify_agent import clarify_agent
from manager_agent import manager_agent



# from research_manager import ResearchManager
load_dotenv(override=True)

async def get_questions(query: str):

    yield "Thinking of some questions that will help to hone my research...", gr.update(value=None), gr.update(value=None), gr.update(value=None), gr.update(value=None) 

    result = await Runner.run(clarify_agent, query)

    questions = "To help me hone my research please answer the following questions:\n\n"
    questions += "\n\n".join([f"{i+1}. {item.question}" for i, item in enumerate(result.final_output.clarifiers)])

    yield questions, gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True, value="Do Research")

async def do_research(query,questions,resp_one, resp_two, resp_three):

    # Combine query with clarifying questions and responses
    research_input = f"Query: {query}"
    if questions:
        research_input += f"\n\nClarifying Questions:\n{questions}"
    if resp_one:
        research_input += f"\n\nResponse 1: {resp_one}"
    if resp_two:
        research_input += f"\n\nResponse 2: {resp_two}"
    if resp_three:
        research_input += f"\n\nResponse 3: {resp_three}"

    trace_id = gen_trace_id()
    with trace("Research trace", trace_id=trace_id):
        print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
        yield f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"

        # Use streaming for real-time output
        result = Runner.run_streamed(manager_agent, research_input)
        
        output_text = ""
        status_updates = []
        
        async for event in result.stream_events():
            if event.type == "raw_response_event":
                # Handle raw response events (token streaming)
                continue
            elif event.type == "agent_updated_stream_event":
                # Agent status updates
                status_msg = f"🔄 {event.new_agent.name} is working...\n"
                status_updates.append(status_msg)
                yield f"{output_text}\n\n**Status Updates:**\n" + "\n".join(status_updates)
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    # Tool is being called
                    tool_name = event.item.raw_item.name
                    status_msg = f"🔧 Calling tool: {tool_name}\n"
                    status_updates.append(status_msg)
                    yield f"{output_text}\n\n**Status Updates:**\n" + "\n".join(status_updates)
                elif event.item.type == "tool_call_output_item":
                    # Tool output received
                    status_msg = f"✅ Tool output received\n"
                    status_updates.append(status_msg)
                    yield f"{output_text}\n\n**Status Updates:**\n" + "\n".join(status_updates)
                elif event.item.type == "message_output_item":
                    # Agent message output
                    if hasattr(event.item, 'output'):
                        output_text += str(event.item.output)
                        yield f"{output_text}\n\n**Status Updates:**\n" + "\n".join(status_updates)
        
    # Return final result
    final_result = result.final_output
    final_output = f"{output_text}\n\n---\n\n**Final Research Plan:**\n{final_result}"
    
    yield final_output



with gr.Blocks(theme=gr.themes.Glass()) as ui:

    gr.Markdown("<h1 style=\"text-align:center\">Deep Research</h1>")
    with gr.Row():
        
        with gr.Column(scale=1):
            gr.Markdown("## Research Input")
            query_textbox = gr.Textbox(label="What topic would you like to research?")
            run_button = gr.Button("Run", variant="primary")
            questions_markdown = gr.Markdown(label="Report")

            q1_textbox = gr.Textbox(label="Question 1:", visible=False, interactive=True)
            q2_textbox = gr.Textbox(label="Question 2:", visible=False, interactive=True)
            q3_textbox = gr.Textbox(label="Question 3:", visible=False, interactive=True)

            q_button = gr.Button("Answer clarifying questions", variant="primary", visible=False)
                
            
        
        with gr.Column(scale=1):
            gr.Markdown("## Research Output")
            research_markdown = gr.Markdown(label="Research")

        query_textbox.submit(fn=get_questions, inputs=query_textbox, outputs=[questions_markdown, q1_textbox, q2_textbox, q3_textbox, q_button])
        run_button.click(fn=get_questions, inputs=query_textbox, outputs=[questions_markdown, q1_textbox, q2_textbox, q3_textbox, q_button])

        q_button.click(fn=do_research, inputs=[query_textbox,questions_markdown,q1_textbox,q2_textbox,q3_textbox], outputs=research_markdown, show_progress=True)


ui.launch(inbrowser=True)