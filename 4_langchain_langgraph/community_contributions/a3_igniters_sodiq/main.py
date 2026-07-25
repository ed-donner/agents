import gradio as gr
from nodes import app

async def chat_with_team(user_message, history):
    bot_message_placeholder = ""
    history.append((user_message, bot_message_placeholder))
    
    initial_state = {"input": user_message, "results": [], "status": "Initializing Team..."}

    async for event in app.astream(initial_state):
        for node_name, state_update in event.items():
            
            if "status" in state_update:
                new_status = state_update["status"]
                
                bot_message_placeholder = f"*{new_status}*"
                history[-1] = (user_message, bot_message_placeholder)
                yield history, "" 

            if "response" in state_update:
                final_answer = state_update["response"]
                history[-1] = (user_message, final_answer)
                yield history, ""


with gr.Blocks(title="Research Team") as ui:
    gr.Markdown("## Research Team")
    gr.Markdown(
        "Ask a complex query (e.g., 'Impact of AI on Nigerian fintech'). "
        "My Planner will break it down, multiple Workers will search in parallel, "
        "and the Re-planner will summarize the results."
    )
    
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Enter your research query here...")
    clear = gr.Button("Clear")

    msg.submit(chat_with_team, [msg, chatbot], [chatbot, msg])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    ui.queue().launch()