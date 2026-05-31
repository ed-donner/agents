"""
Quick test script for RAG system
Run this to verify everything is working
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

from rag_system import RAGSystem, QueryExpander
from evaluation import RAGEvaluator

# Load environment
load_dotenv(override=True)
openai_client = OpenAI()

print("="*60)
print("🧪 RAG System Quick Test")
print("="*60)

# Test 1: Query Expansion
print("\n1️⃣  Testing Query Expansion...")
try:
    expander = QueryExpander(openai_client)
    query = "What are your skills?"
    expanded = expander.expand_query(query, num_variations=2)
    print(f"✓ Original: {query}")
    print(f"✓ Expanded to {len(expanded)} queries")
    for i, q in enumerate(expanded[1:], 1):
        print(f"  {i}. {q}")
except Exception as e:
    print(f"✗ Query expansion failed: {e}")

# Test 2: Document Loading
print("\n2️⃣  Testing Document Loading...")
try:
    # Create simple test documents
    test_docs = {
        "doc1": "I have experience with Python, JavaScript, and SQL. I've worked on ML projects.",
        "doc2": "My education includes a degree in Computer Science. I studied AI and databases.",
        "doc3": "I'm passionate about building scalable systems and working with data."
    }
    
    rag_system = RAGSystem(openai_client, data_dir="data_test")
    rag_system.load_knowledge_base(test_docs, chunk_size=100, overlap=20)
    print("✓ RAG system initialized")
    print(f"✓ Loaded {len(test_docs)} test documents")
except Exception as e:
    print(f"✗ Document loading failed: {e}")
    exit(1)

# Test 3: Retrieval Methods
print("\n3️⃣  Testing Retrieval Methods...")
test_query = "What programming languages?"

methods_to_test = ["bm25", "semantic", "hybrid", "hybrid_rerank"]

for method in methods_to_test:
    try:
        results = rag_system.retriever.retrieve(
            test_query,
            method=method,
            top_k=2
        )
        print(f"✓ {method:15s}: Retrieved {len(results)} documents")
        if results:
            print(f"  Top score: {results[0]['retrieval_score']:.4f}")
    except Exception as e:
        print(f"✗ {method:15s}: Failed - {e}")

# Test 4: End-to-End RAG Query
print("\n4️⃣  Testing End-to-End RAG Query...")
try:
    system_prompt = "You are answering questions about a person's professional background."
    response = rag_system.query(
        "What programming languages do you know?",
        system_prompt,
        method="hybrid_rerank",
        top_k=3
    )
    
    print("✓ Query successful!")
    print(f"✓ Retrieved {len(response['context'])} context documents")
    print(f"✓ Generated answer ({len(response['answer'])} characters)")
    print(f"\nAnswer preview:\n{response['answer'][:200]}...")
except Exception as e:
    print(f"✗ RAG query failed: {e}")

# Test 5: LLM-as-Judge
print("\n5️⃣  Testing LLM-as-Judge...")
try:
    evaluator = RAGEvaluator(openai_client)
    
    # Test relevance judgment
    judge_result = evaluator.llm_as_judge_relevance(
        query="What are your programming skills?",
        document="I have experience with Python, JavaScript, and SQL.",
        context="Professional background"
    )
    
    print("✓ LLM judge evaluation successful")
    print(f"  Relevance score: {judge_result['relevance_score']}/5")
    print(f"  Explanation: {judge_result['explanation']}")
except Exception as e:
    print(f"✗ LLM judge failed: {e}")

# Summary
print("\n" + "="*60)
print("✅ All tests completed!")
print("="*60)
print("\n💡 Next steps:")
print("  1. Add your linkedin.pdf to the me/ folder")
print("  2. Edit me/summary.txt with your information")
print("  3. Update NAME in app.py")
print("  4. Run: python app.py")
print("\n📊 For full evaluation:")
print("  jupyter notebook demo_and_evaluation.ipynb")
print("="*60)

# Cleanup test data
print("\n🧹 Cleaning up test data...")
import shutil
if Path("data_test").exists():
    shutil.rmtree("data_test")
    print("✓ Test data cleaned up")

