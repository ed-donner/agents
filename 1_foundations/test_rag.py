#!/usr/bin/env python3
"""
Test Script for Resume RAG System
Tests the functionality of the RAG system and demonstrates usage
"""

import os
from resume_rag import ResumeRAG
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def test_basic_functionality():
    """Test basic RAG functionality"""
    print("=== Testing Basic RAG Functionality ===\n")
    
    # Initialize RAG system
    rag = ResumeRAG()
    
    # Show collection info
    info = rag.get_collection_info()
    print(f"Collection: {info.get('name', 'Unknown')}")
    print(f"Documents in collection: {info.get('count', 0)}")
    print(f"Database path: {info.get('path', 'Unknown')}\n")
    
    if info.get('count', 0) == 0:
        print("⚠️  No documents found in the collection.")
        print("Please run 'python add_resume.py' first to add your resume.\n")
        return False
    
    return True

def test_search_queries():
    """Test various search queries"""
    print("=== Testing Search Queries ===\n")
    
    rag = ResumeRAG()
    
    # Test queries that might be relevant to a resume
    test_queries = [
        "What is my work experience?",
        "What are my technical skills?",
        "Tell me about my education background",
        "What programming languages do I know?",
        "What projects have I worked on?",
        "What are my achievements?",
        "What is my contact information?",
        "What companies have I worked for?"
    ]
    
    for query in test_queries:
        print(f"🔍 Query: {query}")
        
        # Test search function
        results = rag.search(query, n_results=3)
        
        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results[:2]):  # Show top 2 results
                content = result['content']
                distance = result['distance']
                print(f"   {i+1}. Distance: {distance:.3f}")
                print(f"      Content: {content[:150]}{'...' if len(content) > 150 else ''}")
        else:
            print("   No results found")
        
        print()

def test_context_retrieval():
    """Test context retrieval for RAG"""
    print("=== Testing Context Retrieval ===\n")
    
    rag = ResumeRAG()
    
    test_questions = [
        "What makes me a good candidate for a software engineering role?",
        "What is my educational background?",
        "What are my key accomplishments?"
    ]
    
    for question in test_questions:
        print(f"❓ Question: {question}")
        
        context = rag.get_relevant_context(question, max_context_length=800)
        
        if context:
            print(f"📄 Retrieved context ({len(context)} characters):")
            print(f"   {context[:300]}{'...' if len(context) > 300 else ''}")
        else:
            print("   No relevant context found")
        
        print("-" * 60)

def test_integration():
    """Test integration with the main app"""
    print("=== Testing Integration with Main App ===\n")
    
    try:
        # Import and test the Me class
        from app import Me
        
        print("Creating Me instance (this initializes RAG)...")
        me = Me()
        
        if me.rag:
            print("✅ RAG system successfully integrated with chatbot")
            
            # Test a sample interaction
            print("\n🤖 Testing sample interaction:")
            sample_message = "What are my key technical skills?"
            print(f"User: {sample_message}")
            
            # This would normally go through the full chat pipeline
            # For testing, we'll just check if context retrieval works
            if hasattr(me.rag, 'get_relevant_context'):
                context = me.rag.get_relevant_context(sample_message)
                if context:
                    print(f"✅ Context successfully retrieved ({len(context)} characters)")
                else:
                    print("⚠️  No context retrieved")
        else:
            print("❌ RAG system not initialized in chatbot")
            
    except ImportError as e:
        print(f"❌ Could not import app.py: {e}")
    except Exception as e:
        print(f"❌ Error testing integration: {e}")

def show_usage_instructions():
    """Show instructions for using the system"""
    print("=== Usage Instructions ===\n")
    
    print("📝 Step-by-Step Guide:")
    print("1. Make sure your resume is in Microsoft Word (.docx) format")
    print("2. Run: uv run add_resume.py /path/to/your/resume.docx")
    print("3. Test the system: uv run test_rag.py")
    print("4. Run your chatbot: uv run app.py")
    print()
    
    print("🔧 Available Scripts:")
    print("• add_resume.py - Add your Word resume to the database")
    print("• test_rag.py - Test the RAG system (this script)")
    print("• app.py - Run the enhanced chatbot with RAG")
    print("• resume_rag.py - Core RAG functionality (library)")
    print()
    
    print("💡 Tips:")
    print("• The system works best with detailed, well-structured resumes")
    print("• You can add multiple documents to build a comprehensive knowledge base")
    print("• The RAG system will automatically find relevant information for user queries")
    print("• Context is limited to 1500 characters to stay within token limits")
    print()

def main():
    """Main test function"""
    print("🚀 Resume RAG System Test Suite\n")
    
    # Test basic functionality
    if not test_basic_functionality():
        show_usage_instructions()
        return
    
    # Run all tests
    test_search_queries()
    test_context_retrieval()
    test_integration()
    
    print("=== Test Summary ===")
    print("✅ All tests completed!")
    print("Your RAG system is ready to enhance your career chatbot.")
    print("\nRun 'uv run app.py' to start the enhanced chatbot!")

if __name__ == "__main__":
    main()
