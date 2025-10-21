"""
STEP 3: Run Your Chatbot
=========================

This starts your WindowWolf chatbot with a web interface.

The chatbot will:
- Use RAG to answer questions intelligently
- Record customer contact information via Pushover
- Evaluate responses with Gemini for quality control

Just run this file and your browser will open automatically!
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main WindowWolfApp
from WindowWolfApp import WindowWolf
import gradio as gr


def main():
    print("=" * 60)
    print("WindowWolf Chatbot")
    print("=" * 60)
    print("\nStarting chatbot with RAG system...")
    print("Your browser will open automatically.")
    print("\nPress Ctrl+C to stop the server when done.")
    print("=" * 60)
    
    # Auto-initialize RAG if needed (for deployment)
    try:
        from rag_system.rag_manager import RAGManager
        script_dir = os.path.dirname(os.path.abspath(__file__))
        manager = RAGManager(base_path=script_dir)
        stats = manager.get_system_stats()
        
        if stats.get('total_chunks', 0) == 0:
            print("\nFirst-time setup: Initializing RAG system...")
            print("This may take 30-60 seconds...")
            manager.initialize_documents(force_reload=True)
            print("RAG system initialized successfully!")
    except Exception as e:
        print(f"\nWarning: Could not auto-initialize RAG: {e}")
        print("You may need to run: python 2_initialize_rag.py")
    
    # Initialize the chatbot
    try:
        window_wolf = WindowWolf()
        
        # Create the chat interface
        demo = gr.ChatInterface(
            window_wolf.chat,
            title="Window Wolf - Professional Window Cleaning",
            description="Ask me about ny window cleaning business, or about me!",
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
        
        print("\n" + "=" * 60)
        print("Chatbot is ready!")
        print("=" * 60)
        
        # Launch the interface
        demo.launch()
        
    except KeyboardInterrupt:
        print("\n\nStopping chatbot...")
        print("Goodbye!")
    except Exception as e:
        print(f"\n\nERROR starting chatbot: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you ran: python 2_initialize_rag.py")
        print("2. Check that .env file exists in parent directory")
        print("3. Verify your API keys are set correctly")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

