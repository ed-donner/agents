import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env", override=True)

from rag_system import QueryExpander, HybridRetriever, RAGSystem


def test_query_expansion():
    print("\n" + "="*60)
    print("TEST: Query Expansion")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        expander = QueryExpander(client)
        
        query = "What are your programming skills?"
        expanded = expander.expand_query(query, num_variations=2)
        
        assert isinstance(expanded, list), "Should return a list"
        assert len(expanded) >= 1, "Should have at least original query"
        assert query in expanded, "Should include original query"
        
        print(f"✓ Original: {query}")
        for i, q in enumerate(expanded[1:], 1):
            print(f"✓ Variation {i}: {q}")
        
        print("✅ Query expansion test PASSED")
        return True
    except Exception as e:
        print(f"❌ Query expansion test FAILED: {e}")
        return False


def test_retriever_initialization():
    print("\n" + "="*60)
    print("TEST: Retriever Initialization")
    print("="*60)
    
    try:
        retriever = HybridRetriever(data_dir="data/test_retriever")
        
        assert retriever.embedder is not None, "Embedder should be initialized"
        assert retriever.reranker is not None, "Reranker should be initialized"
        assert retriever.chroma_client is not None, "ChromaDB client should be initialized"
        
        print("✓ Embedder loaded")
        print("✓ Reranker loaded")
        print("✓ ChromaDB client initialized")
        print("✅ Retriever initialization test PASSED")
        return True
    except Exception as e:
        print(f"❌ Retriever initialization test FAILED: {e}")
        return False


def test_chunking():
    print("\n" + "="*60)
    print("TEST: Text Chunking")
    print("="*60)
    
    try:
        retriever = HybridRetriever(data_dir="data/test_chunking")
        
        text = " ".join([f"word{i}" for i in range(100)])
        chunks = retriever.chunk_text(text, chunk_size=20, overlap=5)
        
        assert isinstance(chunks, list), "Should return a list"
        assert len(chunks) > 0, "Should create at least one chunk"
        assert all(isinstance(c, str) for c in chunks), "All chunks should be strings"
        
        print(f"✓ Created {len(chunks)} chunks from {len(text)} character text")
        print(f"✓ First chunk: {len(chunks[0].split())} words")
        print("✅ Chunking test PASSED")
        return True
    except Exception as e:
        print(f"❌ Chunking test FAILED: {e}")
        return False


def test_document_indexing():
    print("\n" + "="*60)
    print("TEST: Document Indexing")
    print("="*60)
    
    try:
        retriever = HybridRetriever(data_dir="data/test_indexing")
        
        test_docs = {
            "doc1": "Python is a high-level programming language. It is widely used for web development and data science.",
            "doc2": "Machine learning involves training models on data. It uses algorithms like neural networks.",
            "doc3": "FastAPI is a modern web framework for Python. It is fast and easy to use."
        }
        
        retriever.index_documents(test_docs, chunk_size=20, overlap=5)
        
        assert retriever.documents is not None, "Documents should be indexed"
        assert len(retriever.documents) > 0, "Should have indexed chunks"
        assert retriever.bm25 is not None, "BM25 index should be created"
        assert retriever.collection is not None, "ChromaDB collection should be created"
        
        print(f"✓ Indexed {len(test_docs)} documents")
        print(f"✓ Created {len(retriever.documents)} chunks")
        print("✓ BM25 index created")
        print("✓ Semantic index created")
        print("✅ Document indexing test PASSED")
        return True
    except Exception as e:
        print(f"❌ Document indexing test FAILED: {e}")
        return False


def test_retrieval_methods():
    print("\n" + "="*60)
    print("TEST: Retrieval Methods")
    print("="*60)
    
    try:
        retriever = HybridRetriever(data_dir="data/test_methods")
        
        test_docs = {
            "doc1": "Python programming language for web development and machine learning applications",
            "doc2": "JavaScript is used for frontend development with React and Vue frameworks",
            "doc3": "SQL databases like PostgreSQL store structured data efficiently"
        }
        
        retriever.index_documents(test_docs, chunk_size=15, overlap=3)
        
        query = "Python programming"
        
        bm25_results = retriever.retrieve_bm25(query, top_k=2)
        assert isinstance(bm25_results, list), "BM25 should return a list"
        print(f"✓ BM25 retrieval: {len(bm25_results)} results")
        
        semantic_results = retriever.retrieve_semantic(query, top_k=2)
        assert isinstance(semantic_results, list), "Semantic should return a list"
        print(f"✓ Semantic retrieval: {len(semantic_results)} results")
        
        hybrid_results = retriever.retrieve_hybrid(query, top_k=2)
        assert isinstance(hybrid_results, list), "Hybrid should return a list"
        print(f"✓ Hybrid retrieval: {len(hybrid_results)} results")
        
        reranked = retriever.rerank(query, hybrid_results, top_k=1)
        assert isinstance(reranked, list), "Reranking should return a list"
        print(f"✓ Reranking: {len(reranked)} results")
        
        print("✅ Retrieval methods test PASSED")
        return True
    except Exception as e:
        print(f"❌ Retrieval methods test FAILED: {e}")
        return False


def test_rag_system():
    print("\n" + "="*60)
    print("TEST: RAG System End-to-End")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        rag_system = RAGSystem(client, data_dir="data/test_rag")
        
        test_docs = {
            "summary": "I am an experienced AI engineer with 5 years of Python development",
            "projects": "Built RAG systems, multi-agent frameworks, and production ML pipelines",
            "stack": "Expert in Python, FastAPI, LangChain, ChromaDB, and OpenAI APIs"
        }
        
        rag_system.load_knowledge_base(test_docs, chunk_size=20, overlap=5)
        
        system_prompt = "Answer questions about professional background."
        response = rag_system.query(
            "What programming languages do you know?",
            system_prompt,
            method="hybrid",
            top_k=3
        )
        
        assert "answer" in response, "Response should contain answer"
        assert "context" in response, "Response should contain context"
        assert "method" in response, "Response should contain method"
        assert len(response["context"]) > 0, "Should retrieve some context"
        
        print(f"✓ Retrieved {len(response['context'])} context documents")
        print(f"✓ Generated answer: {len(response['answer'])} characters")
        print(f"✓ Method used: {response['method']}")
        print("✅ RAG system test PASSED")
        return True
    except Exception as e:
        print(f"❌ RAG system test FAILED: {e}")
        return False


def run_all_tests():
    print("\n" + "="*70)
    print("RUNNING RAG SYSTEM TESTS")
    print("="*70)
    
    tests = [
        test_query_expansion,
        test_retriever_initialization,
        test_chunking,
        test_document_indexing,
        test_retrieval_methods,
        test_rag_system
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("="*70)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

