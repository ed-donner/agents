#!/usr/bin/env python3
"""
AI Visual Art Studio IDE - Main Application
A comprehensive IDE for multi-agent creative pipelines using OpenAI Agents SDK
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.art_studio import ArtStudio
from src.ui.gradio_interface import create_gradio_interface


def main():
    """Main entry point for the AI Visual Art Studio IDE"""
    
    # Load environment variables
    load_dotenv()
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_api_key_here")
        return
    
    try:
        # Initialize the Art Studio
        print("🎨 Initializing AI Visual Art Studio IDE...")
        art_studio = ArtStudio()
        
        # Create and launch the Gradio interface
        print("🚀 Launching Gradio interface...")
        interface = create_gradio_interface(art_studio)
        
        # Launch the interface
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=True,
            show_error=True
        )
        
    except Exception as e:
        print(f"❌ Error starting Art Studio: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
