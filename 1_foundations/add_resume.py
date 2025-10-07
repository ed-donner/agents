#!/usr/bin/env python3
"""
Resume Ingestion Script
Use this script to add your Word resume to the Chroma database
"""

import os
import sys
from resume_rag import ResumeRAG
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def main():
    print("=== Resume RAG Setup ===\n")
    
    # Initialize RAG system
    print("Initializing Resume RAG system...")
    rag = ResumeRAG()
    
    # Show current collection info
    info = rag.get_collection_info()
    print(f"Collection: {info.get('name', 'Unknown')}")
    print(f"Current documents: {info.get('count', 0)}")
    print(f"Database path: {info.get('path', 'Unknown')}\n")
    
    # Get resume file path
    if len(sys.argv) > 1:
        resume_path = sys.argv[1]
    else:
        resume_path = input("Enter the path to your Word resume (.docx): ").strip()
    
    # Check if file exists
    if not os.path.exists(resume_path):
        print(f"Error: File not found: {resume_path}")
        return
    
    if not resume_path.lower().endswith('.docx'):
        print("Warning: File doesn't appear to be a Word document (.docx)")
        proceed = input("Continue anyway? (y/n): ").lower()
        if proceed != 'y':
            return
    
    print(f"\nProcessing resume: {resume_path}")
    print("This may take a moment as we:")
    print("1. Extract text from your Word document")
    print("2. Split it into searchable chunks")
    print("3. Generate embeddings using OpenAI")
    print("4. Store everything in the Chroma database\n")
    
    # Process the resume
    success = rag.add_resume(resume_path)
    
    if success:
        print("✅ Resume successfully added to the knowledge base!")
        
        # Show updated info
        info = rag.get_collection_info()
        print(f"\nUpdated collection info:")
        print(f"Total documents: {info.get('count', 0)}")
        
        # Test with a sample query
        print("\n=== Testing the knowledge base ===")
        test_query = "What are my key skills and experience?"
        print(f"Test query: {test_query}")
        
        context = rag.get_relevant_context(test_query)
        if context:
            print(f"\nRetrieved context (first 300 chars):")
            print(context[:300] + "..." if len(context) > 300 else context)
        else:
            print("No relevant context found")
            
    else:
        print("❌ Failed to add resume to the knowledge base")
        print("Please check the file path and try again")

if __name__ == "__main__":
    main()
