#!/usr/bin/env python3
"""
Deep Research Assistant - Hugging Face Spaces Deployment
A comprehensive AI-powered research assistant with quality assurance.
"""

import os
import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Import the main interface from deep_research.py
from deep_research import ui

if __name__ == "__main__":
    # Launch the interface
    # For Hugging Face Spaces, we don't need inbrowser=True and we want to set share=False
    ui.launch(
        server_name="0.0.0.0",  # Required for Hugging Face Spaces
        server_port=7860,       # Standard port for Gradio on HF Spaces
        share=False,            # Don't create public links on HF Spaces
        inbrowser=False         # Don't try to open browser on server
    ) 