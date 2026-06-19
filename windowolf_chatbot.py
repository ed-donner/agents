#!/usr/bin/env python3
"""
Direct entry point for Hugging Face Spaces
"""

import sys
import os
sys.path.append('My_AIProjects')

# Import and run the app from your organized project
if __name__ == "__main__":
    # Import the app from My_AIProjects
    from My_AIProjects.windowolf_chatbot import Windowolf
    import gradio as gr
    
    # Create the chatbot instance
    windowolf_bot = Windowolf()
    
    # Create the Gradio interface
    demo = gr.ChatInterface(
        windowolf_bot.chat,
        title="Windowolf - Professional Window Cleaning",
        description="Ask me about window cleaning services, pricing, scheduling, or anything else!",
        examples=[
            "What services do you offer?",
            "How much do you charge for window cleaning?",
            "Do you clean gutters too?",
            "What areas do you serve?",
            "How do I schedule an appointment?"
        ],
        cache_examples=False,
        type="messages"
    )
    
    # Launch the interface
    demo.launch()