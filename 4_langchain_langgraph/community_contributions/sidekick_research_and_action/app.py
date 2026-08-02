import gradio as gr
from sidekick import Sidekick

async def setup():
    sidekick = Sidekick()
    await sidekick.setup()
    return sidekick, None  # Return sidekick and initial thread_id

async def process_message(sidekick, thread_id, message, success_criteria, history):
    # Call run_superstep with thread_id
    results, new_thread_id = await sidekick.run_superstep(
        message, success_criteria, history, thread_id
    )
    # Return updated history, sidekick, and thread_id
    return results, sidekick, new_thread_id
    
async def reset():
    new_sidekick = Sidekick()
    await new_sidekick.setup()
    return "", "", [], new_sidekick, None  # Reset thread_id too

async def free_resources(sidekick):
    print("Cleaning up")
    try:
        if sidekick:
            await sidekick.cleanup()  # Now properly async
    except Exception as e:
        print(f"Exception during cleanup: {e}")

with gr.Blocks(title="Multi-Agent Sidekick", theme=gr.themes.Default(primary_hue="emerald")) as ui:
    gr.Markdown("## Multi-Agent Sidekick Personal Co-Worker")
    gr.Markdown("*Powered by specialized Research and Action agents with intelligent coordination*")
    
    # State components
    sidekick = gr.State(delete_callback=free_resources)
    thread_id = gr.State()  # Track conversation thread
    
    with gr.Row():
        chatbot = gr.Chatbot(label="Multi-Agent Sidekick", height=400, type="messages")
    
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False, 
                placeholder="Your request to the Multi-Agent Sidekick",
                autofocus=True
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, 
                placeholder="What are your success criteria? (optional)"
            )
    
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Go!", variant="primary")
    
    with gr.Accordion("How it works", open=False):
        gr.Markdown("""
        **Multi-Agent Architecture:**
        1. **Coordinator** - Analyzes your request and creates an execution plan or responds directly
        2. **Research Agent** - Handles web searches, Wikipedia lookups, and file analysis  
        3. **Action Agent** - Executes Python code, creates files, sends notifications, and automates browsers
        4. **Evaluator** - Combines results and evaluates completion against success criteria
        
        **Smart Routing:**
        - Simple queries get direct responses without invoking agents
        - Complex tasks are intelligently delegated to specialized agents
        - Agents work sequentially, sharing context when needed
        
        **Examples:**
        - "Research Tesla stock and calculate returns on $5000" → Both agents collaborate
        - "Convert meeting-notes.md to PDF" → Action agent handles it
        - "What are current AI trends?" → Research agent investigates
        - "Hello" → Direct response, no agents needed
        """)
    
    # Load initial sidekick and thread_id
    ui.load(setup, [], [sidekick, thread_id])
    
    # Process message with thread_id tracking
    message.submit(
        process_message, 
        [sidekick, thread_id, message, success_criteria, chatbot], 
        [chatbot, sidekick, thread_id]
    )
    success_criteria.submit(
        process_message, 
        [sidekick, thread_id, message, success_criteria, chatbot], 
        [chatbot, sidekick, thread_id]
    )
    go_button.click(
        process_message, 
        [sidekick, thread_id, message, success_criteria, chatbot], 
        [chatbot, sidekick, thread_id]
    )
    
    # Reset everything including thread_id
    reset_button.click(
        reset, 
        [], 
        [message, success_criteria, chatbot, sidekick, thread_id]
    )

ui.launch(inbrowser=True)