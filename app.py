#!/usr/bin/env python3
"""
Hugging Face Spaces app entry point
"""

import sys
import os
sys.path.append('My_AIProjects')

import gradio as gr
from windowolf_chatbot import Windowolf

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
if __name__ == "__main__":
    demo.launch()
