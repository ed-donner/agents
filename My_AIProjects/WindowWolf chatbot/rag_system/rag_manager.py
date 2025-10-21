"""
RAG Manager for WindowWolf App
This module manages the RAG system initialization, document processing, and integration.
"""

import os
import logging
from typing import List, Dict, Optional
from .rag_system import RAGSystem, DocumentProcessor

logger = logging.getLogger(__name__)

class RAGManager:
    """
    Manager class for the RAG system that handles initialization and document processing.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the RAG manager.
        
        Args:
            base_path: Base path for the project (defaults to current directory)
        """
        if base_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.base_path = base_path
        # Store database in the main project directory, not in rag_system subdirectory
        parent_path = os.path.dirname(base_path) if base_path.endswith('rag_system') else base_path
        self.db_path = os.path.join(parent_path, "ww_rag.db")
        self.rag_system = RAGSystem(db_path=self.db_path)
        
        # Define document paths (look in source_documents directory)
        parent_path = os.path.dirname(base_path) if base_path.endswith('rag_system') else base_path
        source_docs_path = os.path.join(parent_path, "source_documents")
        self.document_paths = {
            "pdf": os.path.join(source_docs_path, "WindowWolfChatbot.pdf"),
            "summary": os.path.join(source_docs_path, "WindowWolfSummary.txt")
        }
        
        logger.info(f"RAG Manager initialized with base path: {base_path}")
    
    def initialize_documents(self, force_reload: bool = False) -> Dict[str, str]:
        """
        Initialize the RAG system with existing documents.
        
        Args:
            force_reload: If True, reload documents even if they already exist
            
        Returns:
            Dictionary with document IDs and status
        """
        results = {}
        
        # Check if documents are already loaded
        if not force_reload:
            stats = self.rag_system.get_collection_stats()
            if stats.get("total_chunks", 0) > 0:
                logger.info("Documents already loaded. Use force_reload=True to reload.")
                return {"status": "already_loaded", "chunks": stats.get("total_chunks", 0)}
        
        # Clear existing documents if force reload
        if force_reload:
            self.rag_system.clear_collection()
        
        # Process PDF document
        pdf_path = self.document_paths["pdf"]
        if os.path.exists(pdf_path):
            try:
                content, metadata = DocumentProcessor.process_document(pdf_path)
                if content:
                    doc_id = self.rag_system.add_document(
                        content=content,
                        metadata=metadata,
                        doc_id="window_wolf_pdf"
                    )
                    results["pdf"] = doc_id
                    logger.info(f"Added PDF document: {doc_id}")
                else:
                    logger.warning(f"PDF document is empty: {pdf_path}")
            except Exception as e:
                logger.error(f"Error processing PDF: {e}")
                results["pdf"] = f"error: {e}"
        else:
            logger.warning(f"PDF document not found: {pdf_path}")
            results["pdf"] = "not_found"
        
        # Process summary document
        summary_path = self.document_paths["summary"]
        if os.path.exists(summary_path):
            try:
                content, metadata = DocumentProcessor.process_document(summary_path)
                if content:
                    doc_id = self.rag_system.add_document(
                        content=content,
                        metadata=metadata,
                        doc_id="window_wolf_summary"
                    )
                    results["summary"] = doc_id
                    logger.info(f"Added summary document: {doc_id}")
                else:
                    logger.warning(f"Summary document is empty: {summary_path}")
            except Exception as e:
                logger.error(f"Error processing summary: {e}")
                results["summary"] = f"error: {e}"
        else:
            logger.warning(f"Summary document not found: {summary_path}")
            results["summary"] = "not_found"
        
        # Get final stats
        stats = self.rag_system.get_collection_stats()
        results["total_chunks"] = stats.get("total_chunks", 0)
        results["status"] = "completed"
        
        logger.info(f"Document initialization completed. Total chunks: {results['total_chunks']}")
        return results
    
    def search_relevant_content(self, query: str, n_results: int = 3) -> List[Dict]:
        """
        Search for relevant content based on a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant content chunks
        """
        try:
            results = self.rag_system.search(query, n_results=n_results)
            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error searching for content: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 2000) -> str:
        """
        Get formatted context for a query to be used in RAG.
        
        Args:
            query: User query
            max_context_length: Maximum length of context to return
            
        Returns:
            Formatted context string
        """
        results = self.search_relevant_content(query, n_results=5)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result['content']
            similarity = result['similarity']
            metadata = result['metadata']
            
            # Add source information
            source = metadata.get('file_name', 'Unknown')
            chunk_info = f"[Source: {source}, Relevance: {similarity:.2f}]"
            
            # Format the context
            formatted_content = f"{chunk_info}\n{content}\n"
            
            # Check if adding this content would exceed the limit
            if current_length + len(formatted_content) > max_context_length:
                # Try to truncate the content to fit
                remaining_space = max_context_length - current_length - len(chunk_info) - 10
                if remaining_space > 100:  # Only add if there's meaningful space
                    truncated_content = content[:remaining_space] + "..."
                    formatted_content = f"{chunk_info}\n{truncated_content}\n"
                    context_parts.append(formatted_content)
                break
            
            context_parts.append(formatted_content)
            current_length += len(formatted_content)
        
        return "\n".join(context_parts)
    
    def add_custom_document(self, content: str, doc_id: str, metadata: Dict = None) -> str:
        """
        Add a custom document to the RAG system.
        
        Args:
            content: Document content
            doc_id: Unique document ID
            metadata: Optional metadata
            
        Returns:
            Document ID
        """
        try:
            if metadata is None:
                metadata = {}
            
            metadata.update({
                "type": "custom",
                "added_by": "user"
            })
            
            doc_id = self.rag_system.add_document(
                content=content,
                metadata=metadata,
                doc_id=doc_id
            )
            
            logger.info(f"Added custom document: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Error adding custom document: {e}")
            raise
    
    def get_system_stats(self) -> Dict:
        """
        Get comprehensive system statistics.
        
        Returns:
            Dictionary with system statistics
        """
        try:
            stats = self.rag_system.get_collection_stats()
            
            # Add document-specific information
            pdf_chunks = self.rag_system.get_document_chunks("window_wolf_pdf")
            summary_chunks = self.rag_system.get_document_chunks("window_wolf_summary")
            
            stats.update({
                "pdf_chunks": len(pdf_chunks),
                "summary_chunks": len(summary_chunks),
                "document_paths": self.document_paths,
                "base_path": self.base_path
            })
            
            return stats
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    def test_search(self, test_queries: List[str] = None) -> Dict:
        """
        Test the search functionality with sample queries.
        
        Args:
            test_queries: List of test queries (uses defaults if None)
            
        Returns:
            Dictionary with test results
        """
        if test_queries is None:
            test_queries = [
                "What services does Window Wolf offer?",
                "How much does window cleaning cost?",
                "What equipment is used for cleaning?",
                "What areas do you serve?",
                "How do I schedule an appointment?"
            ]
        
        results = {}
        
        for query in test_queries:
            try:
                search_results = self.search_relevant_content(query, n_results=2)
                results[query] = {
                    "found_chunks": len(search_results),
                    "top_similarity": search_results[0]['similarity'] if search_results else 0,
                    "sources": [r['metadata'].get('file_name', 'Unknown') for r in search_results]
                }
            except Exception as e:
                results[query] = {"error": str(e)}
        
        return results


def initialize_rag_system(base_path: str = None) -> RAGManager:
    """
    Initialize and return a RAG manager instance.
    
    Args:
        base_path: Base path for the project
        
    Returns:
        Initialized RAGManager instance
    """
    manager = RAGManager(base_path)
    
    # Initialize documents
    init_results = manager.initialize_documents()
    logger.info(f"RAG system initialization results: {init_results}")
    
    return manager
