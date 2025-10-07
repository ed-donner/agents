import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager

load_dotenv(override=True)

research_manager = ResearchManager()

async def chat_respond(message: str, history: list):
    if not history:  # First message - research topic
        questions = await research_manager.generate_clarifications(message)
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        response = f"Great! I'll help you research **{message}**.\n\nTo provide the most relevant research, please help me understand what you're looking for by addressing these questions:\n\n{questions_text}\n\nYou can answer any or all of these questions in your next message."
        history.append([message, response])
        yield "", history
    
    elif len(history) == 1:  # Second message - clarifications provided
        research_topic = history[0][0]
        clarifications = message
        
        response = f"Thanks for the clarifications! I'll now research **{research_topic}** with your additional context in mind. Starting the research process..."
        history.append([message, response])
        
        # Start research with clarifications
        async for chunk in research_manager.run(research_topic, clarifications):
            if chunk.startswith("View trace:") or "complete" in chunk.lower():
                continue  # Skip trace and completion messages in chat
            history[-1][1] = f"Thanks for the clarifications! I'll now research **{research_topic}** with your additional context in mind.\n\n{chunk}"
            yield "", history
    
    else:  # Additional messages - just respond normally
        history.append([message, "Research is complete. Please start a new conversation for another research topic."])
        yield "", history

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research Chat")
    gr.Markdown("Enter a research topic to get started. I'll ask clarifying questions to focus the research.")
    
    chatbot = gr.Chatbot(height=500)
    msg = gr.Textbox(label="Message", placeholder="Enter your research topic or respond to my questions...")
    
    msg.submit(chat_respond, [msg, chatbot], [msg, chatbot])

ui.launch(inbrowser=True)

