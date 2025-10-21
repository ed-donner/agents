"""
RAG (Retrieval-Augmented Generation) System for WindowWolf App
This module provides vector database functionality for document retrieval and embedding generation.
"""

import os
import sqlite3
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import hashlib
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    """
    RAG System for document retrieval and embedding generation.
    Uses ChromaDB for vector storage and SentenceTransformers for embeddings.
    """
    
    def __init__(self, db_path: str = "ww_rag.db", collection_name: str = "window_wolf_docs"):
        """
        Initialize the RAG system.
        
        Args:
            db_path: Path to the ChromaDB database
            collection_name: Name of the collection to store documents
        """
        self.db_path = db_path
        self.collection_name = collection_name
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=os.path.dirname(db_path) if os.path.dirname(db_path) else ".",
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "WindowWolf document embeddings"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better retrieval.
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_endings = ['.', '!', '?', '\n\n']
                
                for i in range(end - 1, search_start, -1):
                    if text[i] in sentence_endings:
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as list of floats
        """
        return self.embedding_model.encode(text).tolist()
    
    def add_document(self, content: str, metadata: Dict = None, doc_id: str = None) -> str:
        """
        Add a document to the vector database.
        
        Args:
            content: Document content
            metadata: Optional metadata for the document
            doc_id: Optional custom document ID
            
        Returns:
            Document ID
        """
        if metadata is None:
            metadata = {}
        
        # Generate document ID if not provided
        if doc_id is None:
            doc_id = hashlib.md5(content.encode()).hexdigest()
        
        # Chunk the document
        chunks = self.chunk_text(content)
        
        # Prepare data for ChromaDB
        chunk_ids = []
        chunk_embeddings = []
        chunk_metadatas = []
        chunk_documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "doc_id": doc_id,
                "added_at": datetime.now().isoformat()
            })
            
            chunk_ids.append(chunk_id)
            chunk_embeddings.append(self.generate_embedding(chunk))
            chunk_metadatas.append(chunk_metadata)
            chunk_documents.append(chunk)
        
        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            embeddings=chunk_embeddings,
            metadatas=chunk_metadatas,
            documents=chunk_documents
        )
        
        logger.info(f"Added document {doc_id} with {len(chunks)} chunks")
        return doc_id
    
    def search(self, query: str, n_results: int = 5, filter_metadata: Dict = None) -> List[Dict]:
        """
        Search for relevant documents based on a query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results with content, metadata, and similarity scores
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0,
                    'similarity': 1 - results['distances'][0][i] if results['distances'] else 1
                }
                formatted_results.append(result)
        
        return formatted_results
    
    def get_document_chunks(self, doc_id: str) -> List[Dict]:
        """
        Get all chunks for a specific document.
        
        Args:
            doc_id: Document ID
            
        Returns:
            List of document chunks
        """
        results = self.collection.get(
            where={"doc_id": doc_id}
        )
        
        chunks = []
        if results['documents']:
            for i, doc in enumerate(results['documents']):
                chunk = {
                    'content': doc,
                    'metadata': results['metadatas'][i] if results['metadatas'] else {},
                    'id': results['ids'][i] if results['ids'] else None
                }
                chunks.append(chunk)
        
        # Sort by chunk index
        chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0))
        return chunks
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"doc_id": doc_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted document {doc_id} with {len(results['ids'])} chunks")
                return True
            else:
                logger.warning(f"No chunks found for document {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "db_path": self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection(name=self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "WindowWolf document embeddings"}
            )
            logger.info(f"Cleared collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False


class DocumentProcessor:
    """
    Utility class for processing different types of documents.
    """
    
    @staticmethod
    def process_pdf(file_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            return ""
    
    @staticmethod
    def process_text_file(file_path: str) -> str:
        """
        Read text from a text file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error reading text file {file_path}: {e}")
            return ""
    
    @staticmethod
    def process_document(file_path: str) -> Tuple[str, Dict]:
        """
        Process a document file and return content with metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (content, metadata)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        metadata = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_type": file_ext,
            "processed_at": datetime.now().isoformat()
        }
        
        if file_ext == '.pdf':
            content = DocumentProcessor.process_pdf(file_path)
        elif file_ext in ['.txt', '.md']:
            content = DocumentProcessor.process_text_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            content = ""
        
        return content, metadata
