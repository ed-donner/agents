"""Gradio user interface for the interview prep agent"""

import uuid
import gradio as gr
from langchain_core.messages import HumanMessage
from src.config import UI_TITLE, UI_SUBTITLE, UI_HEIGHT, UI_PLACEHOLDER
from src.graph import build_graph


# Global state
THREAD_ID = "test-thread"
graph = build_graph()


def reset():
    """Reset conversation by creating new thread ID"""
    global THREAD_ID
    THREAD_ID = str(uuid.uuid4())
    return None, ""


def compat_message(message: str, owner: str) -> dict:
    """
    Create Gradio-compatible message dict
    
    Args:
        message: Message content
        owner: "user" or "assistant"
        
    Returns:
        Message dict for Gradio chatbot
    """
    return {"role": owner, "content": message}


async def chat(message: str, history: list):
    """
    Handle chat messages and stream responses
    
    Args:
        message: User's message
        history: Chat history
        
    Yields:
        Updated chat history
    """
    if not message.strip():
        yield history
        return
    
    try:
        # Show thinking indicator
        history.append(compat_message(message, "user"))
        history.append(compat_message("⏳ Processing...", "assistant"))
        yield history
        
        # Run graph
        config = {"configurable": {"thread_id": THREAD_ID}}
        state = {"messages": [HumanMessage(content=message)]}
        
        result = None
        async for event in graph.astream(state, config, stream_mode="values"):
            result = event
        
        # Update last message with real response
        if result and "messages" in result and len(result["messages"]) > 0:
            history[-1] = compat_message(result["messages"][-1].content, "assistant")
        else:
            history[-1] = compat_message("No response generated.", "assistant")
        
        yield history
        
    except Exception as e:
        history[-1] = compat_message(f"❌ Error: {str(e)}", "assistant")
        yield history


def create_app():
    """
    Create and configure Gradio application
    
    Returns:
        Gradio Blocks app
    """
    with gr.Blocks(theme=gr.themes.Soft(), title="Interview Prep") as app:
        gr.Markdown("# 🎯 Interview Prep Agent")
        gr.Markdown("""
        AI-powered interview preparation assistant
        
        ✅ **Personalized prep guides** tailored to your role  
        🏢 **Company research** from live website data  
        📺 **YouTube recommendations** for interview tips  
        """)
        
        chatbot = gr.Chatbot(height=UI_HEIGHT, type="messages")
        msg = gr.Textbox(placeholder=UI_PLACEHOLDER, show_label=False)
        clear = gr.Button("🔄 Reset")
        
        # Event handlers
        msg.submit(chat, [msg, chatbot], chatbot, queue=True)
        msg.submit(lambda: "", outputs=msg)
        clear.click(reset, None, [chatbot, msg])
    
    return app

