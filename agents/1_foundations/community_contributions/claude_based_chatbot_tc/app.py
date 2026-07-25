"""
Claude-based Chatbot with Tools

This app creates a chatbot using Anthropic's Claude model that represents
a professional profile based on LinkedIn data and other personal information.

Features:
- PDF resume parsing
- Push notifications
- Function calling with tools
- Professional representation
"""
import gradio as gr
from modules.chat import chat_function

# Wrapper function that only returns the message, not the state
def chat_wrapper(message, history, state=None):
    result, new_state = chat_function(message, history, state)
    return result

def main():
    # Create the chat interface
    chat_interface = gr.ChatInterface(
        fn=chat_wrapper,  # Use the wrapper function
        type="messages",
        additional_inputs=[gr.State()]
    )
    
    # Launch the interface
    chat_interface.launch()

if __name__ == "__main__":
    main()