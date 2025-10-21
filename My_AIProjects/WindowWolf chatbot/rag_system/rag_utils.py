"""
RAG Utilities for WindowWolf App
This module provides command-line utilities for managing the RAG system.
"""

import os
import sys
import argparse
import json
from typing import List, Dict
from .rag_manager import RAGManager

def main():
    """Main CLI interface for RAG utilities."""
    parser = argparse.ArgumentParser(description="WindowWolf RAG System Utilities")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize RAG system with documents')
    init_parser.add_argument('--force', action='store_true', help='Force reload documents')
    init_parser.add_argument('--path', type=str, help='Base path for documents')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search the RAG system')
    search_parser.add_argument('query', type=str, help='Search query')
    search_parser.add_argument('--results', type=int, default=5, help='Number of results')
    search_parser.add_argument('--path', type=str, help='Base path for documents')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show RAG system statistics')
    stats_parser.add_argument('--path', type=str, help='Base path for documents')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test RAG system with sample queries')
    test_parser.add_argument('--path', type=str, help='Base path for documents')
    
    # Add document command
    add_parser = subparsers.add_parser('add', help='Add a custom document')
    add_parser.add_argument('content', type=str, help='Document content')
    add_parser.add_argument('doc_id', type=str, help='Document ID')
    add_parser.add_argument('--path', type=str, help='Base path for documents')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all documents from RAG system')
    clear_parser.add_argument('--path', type=str, help='Base path for documents')
    clear_parser.add_argument('--confirm', action='store_true', help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Get base path
    base_path = args.path if hasattr(args, 'path') and args.path else None
    
    try:
        if args.command == 'init':
            initialize_rag_system(base_path, force_reload=args.force)
        elif args.command == 'search':
            search_rag_system(base_path, args.query, args.results)
        elif args.command == 'stats':
            show_rag_stats(base_path)
        elif args.command == 'test':
            test_rag_system(base_path)
        elif args.command == 'add':
            add_custom_document(base_path, args.content, args.doc_id)
        elif args.command == 'clear':
            clear_rag_system(base_path, args.confirm)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def initialize_rag_system(base_path: str = None, force_reload: bool = False):
    """Initialize the RAG system with documents."""
    print("Initializing RAG system...")
    manager = RAGManager(base_path=base_path)
    
    results = manager.initialize_documents(force_reload=force_reload)
    
    print("\nInitialization Results:")
    print(json.dumps(results, indent=2))
    
    if results.get('status') == 'completed':
        print(f"\n✅ RAG system initialized successfully!")
        print(f"Total chunks: {results.get('total_chunks', 0)}")
    elif results.get('status') == 'already_loaded':
        print(f"\n✅ Documents already loaded!")
        print(f"Total chunks: {results.get('chunks', 0)}")
        if force_reload:
            print("Use --force flag to reload documents")

def search_rag_system(base_path: str = None, query: str = None, n_results: int = 5):
    """Search the RAG system."""
    print(f"Searching for: '{query}'")
    manager = RAGManager(base_path=base_path)
    
    results = manager.search_relevant_content(query, n_results=n_results)
    
    if not results:
        print("No results found.")
        return
    
    print(f"\nFound {len(results)} results:")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        print(f"Similarity: {result['similarity']:.3f}")
        print(f"Source: {result['metadata'].get('file_name', 'Unknown')}")
        print(f"Content: {result['content'][:200]}{'...' if len(result['content']) > 200 else ''}")
        print("-" * 40)

def show_rag_stats(base_path: str = None):
    """Show RAG system statistics."""
    print("RAG System Statistics:")
    print("=" * 40)
    
    manager = RAGManager(base_path=base_path)
    stats = manager.get_system_stats()
    
    print(json.dumps(stats, indent=2))

def test_rag_system(base_path: str = None):
    """Test the RAG system with sample queries."""
    print("Testing RAG system with sample queries...")
    print("=" * 50)
    
    manager = RAGManager(base_path=base_path)
    test_results = manager.test_search()
    
    for query, result in test_results.items():
        print(f"\nQuery: {query}")
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Found {result['found_chunks']} chunks")
            print(f"   Top similarity: {result['top_similarity']:.3f}")
            print(f"   Sources: {', '.join(result['sources'])}")

def add_custom_document(base_path: str = None, content: str = None, doc_id: str = None):
    """Add a custom document to the RAG system."""
    print(f"Adding custom document: {doc_id}")
    
    manager = RAGManager(base_path=base_path)
    result = manager.add_custom_document(content, doc_id)
    
    print(f"✅ Document added successfully: {result}")

def clear_rag_system(base_path: str = None, confirm: bool = False):
    """Clear all documents from the RAG system."""
    if not confirm:
        response = input("Are you sure you want to clear all documents? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    print("Clearing RAG system...")
    manager = RAGManager(base_path=base_path)
    
    success = manager.rag_system.clear_collection()
    
    if success:
        print("✅ RAG system cleared successfully!")
    else:
        print("❌ Failed to clear RAG system")

if __name__ == "__main__":
    main()
