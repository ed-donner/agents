"""
STEP 2: Initialize RAG System
==============================

This loads your documents into the vector database.

Run this:
1. ONCE when you first set up the chatbot
2. Anytime you update your source documents (PDF or summary)

Your data persists - you won't lose it when you restart your computer!
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_system.rag_manager import RAGManager


def main():
    print("=" * 60)
    print("STEP 2: Initialize RAG System")
    print("=" * 60)
    print("\nThis will load your documents into the vector database.")
    print("Your documents:")
    print("  - source_documents/WindowWolfChatbot.pdf")
    print("  - source_documents/WindowWolfSummary.txt")
    print("\n" + "-" * 60)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Initialize RAG manager
    print("\nInitializing RAG Manager...")
    manager = RAGManager(base_path=script_dir)
    
    # Check current stats
    stats = manager.get_system_stats()
    current_chunks = stats.get('total_chunks', 0)
    
    if current_chunks > 0:
        print(f"\nFound existing data: {current_chunks} chunks already loaded")
        print("\nWhat would you like to do?")
        print("1. Keep existing data (recommended)")
        print("2. Reload all documents (use if you updated your PDFs)")
        
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "2":
            force_reload = True
            print("\nReloading all documents...")
        else:
            force_reload = False
            print("\nKeeping existing data...")
    else:
        print("\nNo existing data found. Loading documents for first time...")
        force_reload = True
    
    if force_reload:
        print("\nProcessing documents (this may take 30-60 seconds)...")
        results = manager.initialize_documents(force_reload=True)
        
        print("\n" + "=" * 60)
        print("Initialization Complete!")
        print("=" * 60)
        print(f"Status: {results.get('status', 'unknown')}")
        print(f"Total chunks created: {results.get('total_chunks', 0)}")
        print(f"PDF status: {results.get('pdf', 'not processed')}")
        print(f"Summary status: {results.get('summary', 'not processed')}")
        
        # Test search
        print("\n" + "-" * 60)
        print("Testing search functionality...")
        print("-" * 60)
        
        test_query = "What services does Window Wolf offer?"
        context = manager.get_context_for_query(test_query)
        
        if context:
            print(f"\nTest Query: '{test_query}'")
            print("SUCCESS: RAG system is working!")
            print(f"Retrieved {len(context)} characters of relevant context")
        else:
            print("\nWARNING: No context retrieved. Something might be wrong.")
    else:
        print("\nSkipping reload - using existing data.")
    
    print("\n" + "=" * 60)
    print("RAG System Ready!")
    print("=" * 60)
    print("\nNext step: Run your chatbot")
    print("Command: python 3_run_chatbot.py")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

