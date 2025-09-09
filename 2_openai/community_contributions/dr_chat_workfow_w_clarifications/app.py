import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

conversation_history = ["Research Manager: Enter your query"]
next_reply_type = "query"   
research_manager = None

def reset_state():
    global conversation_history, next_reply_type, research_manager
    conversation_history = ["Research Manager: Enter your query"]
    next_reply_type = "query"
    research_manager = None
    return "Research Manager: Enter your query", "", gr.update(visible=True, value=""), gr.update(visible=True, interactive=True), gr.update(visible=False), gr.update(visible=False)

async def handle_input(user_input: str):
    global conversation_history, next_reply_type, research_manager
    
    conversation_history.append(f"You: {user_input}")

    if research_manager is None:
        research_manager = ResearchManager()
    
    # disable and hide the input button while the research manager is working
    yield "\n\n".join(conversation_history), "", gr.update(visible=False), gr.update(visible=False, interactive=False), gr.update(visible=False), gr.update(visible=True)
    
    # the research manager mantains an SQLLite session internally so we only need to pass the new input and type of the input
    result = await research_manager.run(user_input, next_reply_type)
    
    if result.type == "follow_up":
        questions_text = "\n".join([f"{q}" for q in result.questions])
        conversation_history.append(f"Research Manager: {questions_text}")
        next_reply_type = "clarification"
        #re-enable and show the input button and clear input box
        yield "\n\n".join(conversation_history), "", gr.update(visible=True, value=""), gr.update(visible=True, interactive=True), gr.update(visible=False), gr.update(visible=False)
    else:
        #re-enable hide input box and submit button, show reset button
        yield "\n\n".join(conversation_history), result.content, gr.update(visible=False, value=""), gr.update(visible=False, interactive=True), gr.update(visible=True), gr.update(visible=False)

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")
    
    # Conversation history
    history = gr.Markdown(value="Research Manager: Enter your query")
    
    input_box = gr.Textbox(label="Your reply:", placeholder="Type your query or response...")
    submit_button = gr.Button("Submit", variant="primary")
    reset_button = gr.Button("Reset", variant="secondary", visible=False)
    processing_label = gr.Markdown("**Processing...**", visible=False)    
    report = gr.Markdown(label="Report")
    
    submit_button.click(fn=handle_input, inputs=input_box, outputs=[history, report, input_box, submit_button, reset_button, processing_label])
    input_box.submit(fn=handle_input, inputs=input_box, outputs=[history, report, input_box, submit_button, reset_button, processing_label])
    
    reset_button.click(fn=reset_state, outputs=[history, report, input_box, submit_button, reset_button, processing_label])

ui.launch()
