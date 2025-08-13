import os
import gradio as gr
from src.ui.gradio_app import create_gradio_interface
from src.utils.config import Config

def main():
    """Main entry point for the transcript summarizer application."""
    # Load configuration
    config = Config()
    
    print("🚀 Starting Transcript Summarizer...")
    print(f"✨ LLM Provider: {config.llm_provider.capitalize()}")
    if config.llm_provider == "ollama":
        print(f"📡 Ollama URL: {config.ollama_base_url}")
        print(f"🤖 Ollama Model: {config.ollama_model_name}")
    elif config.llm_provider == "gemini":
        print(f"🔑 Gemini API Key: {'Set' if config.gemini_api_key else 'Not Set'}")
        print(f"🤖 Gemini Model: {config.gemini_model_name}")
    print(f"🌐 Gradio Port: {config.gradio_port}")
    
    # Create and launch Gradio interface
    interface = create_gradio_interface(config)
    
    # Launch the application
    interface.launch(
        server_name="0.0.0.0",
        server_port=config.gradio_port,
        share=False,
        show_error=True
    )

if __name__ == "__main__":
    main()
