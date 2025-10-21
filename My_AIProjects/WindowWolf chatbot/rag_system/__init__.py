"""
WindowWolf RAG System Package

This package provides RAG (Retrieval-Augmented Generation) functionality
for the WindowWolf chatbot application.

Modules:
- rag_system: Core RAG functionality with vector database and embeddings
- rag_manager: High-level management and integration
- rag_utils: Command-line utilities for system management
"""

from .rag_system import RAGSystem, DocumentProcessor
from .rag_manager import RAGManager, initialize_rag_system

__version__ = "1.0.0"
__author__ = "WindowWolf Development Team"

__all__ = [
    "RAGSystem",
    "DocumentProcessor", 
    "RAGManager",
    "initialize_rag_system"
]
