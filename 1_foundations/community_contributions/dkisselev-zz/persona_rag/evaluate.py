#!/usr/bin/env python3
"""
Evaluation and Hyperparameter Tuning for Persona RAG
"""
import os
import sys
import json
import random
import time
import shutil
import argparse
import math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

matplotlib.use('Agg')  # Non-interactive backend

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from answer import answer_question, fetch_context

load_dotenv(override=True)

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
FACEBOOK_DATA = DATA_DIR / "processed_facebook_data.json"
LINKEDIN_DATA = DATA_DIR / "processed_linkedin_data.json"
TESTS_FILE = SCRIPT_DIR / "tests.jsonl"

# Initialize OpenAI client for answer evaluation
client = OpenAI()
MODEL = "gpt-4o-mini"

class TestQuestion(BaseModel):
    """A test question with expected keywords and reference answer"""
    question: str = Field(description="The question to ask the RAG system")
    keywords: list[str] = Field(description="Keywords that must appear in retrieved context")
    reference_answer: str = Field(description="The reference answer for this question")
    category: str = Field(description="Question category")

class RetrievalEval(BaseModel):
    """Evaluation metrics for retrieval performance"""
    mrr: float = Field(description="Mean Reciprocal Rank - average across all keywords")
    ndcg: float = Field(description="Normalized Discounted Cumulative Gain (binary relevance)")
    keywords_found: int = Field(description="Number of keywords found in top-k results")
    total_keywords: int = Field(description="Total number of keywords to find")
    keyword_coverage: float = Field(description="Percentage of keywords found")

class AnswerEval(BaseModel):
    """LLM-as-a-judge evaluation of answer quality"""
    feedback: str = Field(description="1 sentence feedback on the answer quality")
    accuracy: float = Field(description="How factually correct is the answer? 1 (wrong) to 5 (perfect)")
    completeness: float = Field(description="How complete is the answer? 1 (missing key info) to 5 (comprehensive)")
    relevance: float = Field(description="How relevant is the answer? 1 (off-topic) to 5 (directly addresses question)")


def load_json_data(filepath):
    """Load JSON data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_tests():
    """Load test questions from JSONL file"""
    tests = []
    with open(TESTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line.strip())
            tests.append(TestQuestion(**data))
    return tests

def create_simple_docs(facebook_items, linkedin_items):
    """Create simple documents from data for hyperparameter tuning"""
    docs = []
    
    # Group LinkedIn by type
    by_source = {}
    for item in linkedin_items:
        source = item.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item['text'])
    
    for source, texts in by_source.items():
        docs.append(Document(
            page_content="\n".join(texts),
            metadata={'source': 'linkedin', 'data_type': source}
        ))
    
    # Group Facebook by source
    by_source = {}
    for item in facebook_items:
        source = item.get('source', 'unknown')
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(item['text'])
    
    for source, texts in by_source.items():
        # Batch in groups of 20
        for i in range(0, len(texts), 20):
            batch = texts[i:i+20]
            docs.append(Document(
                page_content="\n".join(batch),
                metadata={'source': 'facebook', 'data_type': source}
            ))
    
    return docs

def create_chunks_with_size(documents, chunk_size, chunk_overlap_ratio=0.2):
    """Create chunks with specified size"""
    overlap = int(chunk_size * chunk_overlap_ratio)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        is_separator_regex=False
    )
    return text_splitter.split_documents(documents)

def calculate_mrr_simple(keyword: str, retrieved_docs: list) -> float:
    """Calculate reciprocal rank for a keyword"""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0

def evaluate_chunks(chunks, tests, chunk_size, embeddings_model="thenlper/gte-small", k=9):
    """Evaluate chunks with given parameters"""
    db_path = f"temp_db_{int(time.time())}"
    
    try:
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=db_path
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        
        mrr_scores = []
        for test in tests:
            docs = retriever.invoke(test.question)
            test_mrr = np.mean([calculate_mrr_simple(kw, docs) for kw in test.keywords])
            mrr_scores.append(test_mrr)
        
        avg_mrr = np.mean(mrr_scores)
        
    finally:
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
    
    return avg_mrr

def run_hyperparameter_tuning(chunk_sizes, k_values, sample_size=20):
    """Run hyperparameter tuning experiments"""
    print("=" * 80)
    print("HYPERPARAMETER TUNING")
    print("=" * 80)
    
    # Load data
    print("\nLoading data...")
    facebook_items = load_json_data(FACEBOOK_DATA)
    linkedin_items = load_json_data(LINKEDIN_DATA)
    documents = create_simple_docs(facebook_items, linkedin_items)
    print(f"   ✓ Created {len(documents)} base documents")
    
    # Load and sample tests
    print("\nLoading test questions...")
    all_tests = load_tests()
    random.seed(42)
    sampled_tests = random.sample(all_tests, min(sample_size, len(all_tests)))
    print(f"   ✓ Sampled {len(sampled_tests)} tests for evaluation")
    
    # Experiment 1: Chunk Size Optimization
    print("\nChunk Size Optimization")
    print("-" * 80)
    
    chunk_results = []
    
    for size in chunk_sizes:
        print(f"\n   Testing chunk_size={size}...")
        start = time.time()
        
        chunks = create_chunks_with_size(documents, size)
        print(f"     Created {len(chunks)} chunks")
        
        mrr = evaluate_chunks(chunks, sampled_tests, size)
        elapsed = time.time() - start
        
        chunk_results.append({
            'chunk_size': size,
            'num_chunks': len(chunks),
            'mrr': mrr,
            'time_seconds': elapsed
        })
        print(f"     MRR: {mrr:.4f}, Time: {elapsed:.1f}s")
    
    # Plot chunk size results
    chunk_df = pd.DataFrame(chunk_results)
    best_chunk = chunk_df.loc[chunk_df['mrr'].idxmax()]
    print(f"\n   Best chunk size: {best_chunk['chunk_size']} (MRR: {best_chunk['mrr']:.4f})")
    
    plot_chunk_results(chunk_df, best_chunk)
    
    # Experiment 2: K Value Optimization
    print("\nK Value Optimization")
    print("-" * 80)
    print(f"\n   Using optimal chunk size: {best_chunk['chunk_size']}")
    
    optimal_chunks = create_chunks_with_size(documents, int(best_chunk['chunk_size']))
    print(f"   Created {len(optimal_chunks)} chunks")
    
    k_results = []
    
    for k in k_values:
        print(f"\n   Testing K={k}...")
        start = time.time()
        
        mrr = evaluate_chunks(optimal_chunks, sampled_tests, int(best_chunk['chunk_size']), k=k)
        elapsed = time.time() - start
        
        k_results.append({
            'k': k,
            'mrr': mrr,
            'time_seconds': elapsed
        })
        print(f"     MRR: {mrr:.4f}, Time: {elapsed:.1f}s")
    
    # Plot K value results
    k_df = pd.DataFrame(k_results)
    best_k = k_df.loc[k_df['mrr'].idxmax()]
    print(f"\n   Best K value: {best_k['k']} (MRR: {best_k['mrr']:.4f})")
    
    plot_k_results(k_df, best_k)
    
    # Save results
    results = {
        'best_chunk_size': int(best_chunk['chunk_size']),
        'best_chunk_mrr': float(best_chunk['mrr']),
        'best_k': int(best_k['k']),
        'best_k_mrr': float(best_k['mrr']),
        'chunk_results': chunk_results,
        'k_results': k_results
    }
    
    results_path = SCRIPT_DIR / 'hyperparameter_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print_tuning_summary(chunk_df, k_df, best_chunk, best_k)
    
    return results

def plot_chunk_results(chunk_df, best_chunk):
    """Plot chunk size optimization results"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Chunk Size Optimization Results', fontsize=16, fontweight='bold')
    
    # MRR
    axes[0, 0].plot(chunk_df['chunk_size'], chunk_df['mrr'], 'o-', linewidth=2, markersize=8, color='blue')
    axes[0, 0].set_xlabel('Chunk Size (chars)')
    axes[0, 0].set_ylabel('MRR')
    axes[0, 0].set_title('MRR by Chunk Size')
    axes[0, 0].grid(True, alpha=0.3)
    axes[0, 0].axvline(best_chunk['chunk_size'], color='red', linestyle='--', alpha=0.7, label='Best')
    axes[0, 0].legend()
    
    # Number of chunks
    axes[0, 1].bar(chunk_df['chunk_size'], chunk_df['num_chunks'], color='orange', alpha=0.7)
    axes[0, 1].set_xlabel('Chunk Size (chars)')
    axes[0, 1].set_ylabel('Number of Chunks')
    axes[0, 1].set_title('Chunks Created')
    axes[0, 1].grid(True, alpha=0.3, axis='y')
    
    # Processing time
    axes[1, 0].bar(chunk_df['chunk_size'], chunk_df['time_seconds'], color='red', alpha=0.7)
    axes[1, 0].set_xlabel('Chunk Size (chars)')
    axes[1, 0].set_ylabel('Time (seconds)')
    axes[1, 0].set_title('Processing Time')
    axes[1, 0].grid(True, alpha=0.3, axis='y')
    
    # Summary table
    axes[1, 1].axis('off')
    table_data = [[f"{row['chunk_size']}", f"{row['num_chunks']}", f"{row['mrr']:.3f}", f"{row['time_seconds']:.1f}s"] 
                  for _, row in chunk_df.iterrows()]
    table = axes[1, 1].table(
        cellText=table_data,
        colLabels=['Size', 'Chunks', 'MRR', 'Time'],
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    axes[1, 1].set_title('Summary Table', pad=20)
    
    plt.tight_layout()
    plot_path = SCRIPT_DIR / 'hyperparameter_chunk_size.png'
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n   ✓ Saved plot: {plot_path}")
    plt.close()

def plot_k_results(k_df, best_k):
    """Plot K value optimization results"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('K Value Optimization Results', fontsize=16, fontweight='bold')
    
    # MRR by K
    axes[0].plot(k_df['k'], k_df['mrr'], 'o-', linewidth=2, markersize=8, color='green')
    axes[0].set_xlabel('K (Top-K Documents)')
    axes[0].set_ylabel('MRR')
    axes[0].set_title('MRR by K Value')
    axes[0].grid(True, alpha=0.3)
    axes[0].axvline(best_k['k'], color='red', linestyle='--', alpha=0.7, label='Best')
    axes[0].legend()
    
    # Results table
    axes[1].axis('off')
    table_data = [[f"{row['k']}", f"{row['mrr']:.3f}", f"{row['time_seconds']:.1f}s"] 
                  for _, row in k_df.iterrows()]
    table = axes[1].table(
        cellText=table_data,
        colLabels=['K', 'MRR', 'Time'],
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axes[1].set_title('K Value Summary', pad=20)
    
    plt.tight_layout()
    k_plot_path = SCRIPT_DIR / 'hyperparameter_k_value.png'
    plt.savefig(k_plot_path, dpi=150, bbox_inches='tight')
    print(f"\n   ✓ Saved plot: {k_plot_path}")
    plt.close()

def print_tuning_summary(chunk_df, k_df, best_chunk, best_k):
    """Print tuning summary"""
    print("\n" + "=" * 80)
    print("HYPERPARAMETER TUNING SUMMARY")
    print("=" * 80)
    print(f"\n🔹 Best Chunk Size: {best_chunk['chunk_size']}")
    print(f"   MRR: {best_chunk['mrr']:.4f}")
    print(f"   Chunks: {best_chunk['num_chunks']}")
    print(f"   Time: {best_chunk['time_seconds']:.1f}s")
    
    print(f"\n🔹 Best K Value: {best_k['k']}")
    print(f"   MRR: {best_k['mrr']:.4f}")
    print(f"   Time: {best_k['time_seconds']:.1f}s")
    
    print("\n" + "=" * 80)
    print("Next steps:")
    print("  1. Update ingest.py with optimal chunk_size")
    print("  2. Update answer.py with optimal FINAL_K value")
    print("  3. Re-run data ingestion: python ingest.py")
    print("  4. Run evaluation: python evaluate.py --eval")
    print("=" * 80)

def calculate_mrr(keyword: str, retrieved_docs: list) -> float:
    """Calculate reciprocal rank for a single keyword (case-insensitive)"""
    keyword_lower = keyword.lower()
    for rank, doc in enumerate(retrieved_docs, start=1):
        if keyword_lower in doc.page_content.lower():
            return 1.0 / rank
    return 0.0

def calculate_dcg(relevances: list[int], k: int) -> float:
    """Calculate Discounted Cumulative Gain"""
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)  # i+2 because rank starts at 1
    return dcg

def calculate_ndcg(keyword: str, retrieved_docs: list, k: int = 10) -> float:
    """Calculate nDCG for a single keyword (binary relevance, case-insensitive)"""
    keyword_lower = keyword.lower()
    
    # Binary relevance: 1 if keyword found, 0 otherwise
    relevances = [
        1 if keyword_lower in doc.page_content.lower() else 0 
        for doc in retrieved_docs[:k]
    ]
    
    # DCG
    dcg = calculate_dcg(relevances, k)
    
    # Ideal DCG (best case: keyword in first position)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = calculate_dcg(ideal_relevances, k)
    
    return dcg / idcg if idcg > 0 else 0.0

def evaluate_retrieval(test: TestQuestion, k: int = 10) -> RetrievalEval:
    """Evaluate retrieval performance for a test question"""
    # Retrieve documents
    retrieved_docs = fetch_context(test.question)
    
    # Calculate MRR (average across all keywords)
    mrr_scores = [calculate_mrr(keyword, retrieved_docs) for keyword in test.keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
    
    # Calculate nDCG (average across all keywords)
    ndcg_scores = [calculate_ndcg(keyword, retrieved_docs, k) for keyword in test.keywords]
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    
    # Calculate keyword coverage
    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(test.keywords)
    keyword_coverage = (keywords_found / total_keywords * 100) if total_keywords > 0 else 0.0
    
    return RetrievalEval(
        mrr=avg_mrr,
        ndcg=avg_ndcg,
        keywords_found=keywords_found,
        total_keywords=total_keywords,
        keyword_coverage=keyword_coverage,
    )

def evaluate_answer(test: TestQuestion) -> tuple[AnswerEval, str, list]:
    """Evaluate answer quality using LLM-as-a-judge"""
    # Get RAG response
    generated_answer, retrieved_docs = answer_question(test.question)
    
    # Format context for judge
    context_str = "\\n\\n".join([
        f"Source: {doc.metadata.get('source', 'unknown')}\\n{doc.page_content}" 
        for doc in retrieved_docs
    ])
    
    # LLM judge prompt
    judge_messages = [
        {
            "role": "system",
            "content": "You are an expert evaluator assessing the quality of AI-generated answers. Evaluate the generated answer by comparing it to the reference answer and verifying it against the retrieved context.",
        },
        {
            "role": "user",
            "content": f"""Question: {test.question}

Retrieved Context:
{context_str}

Generated Answer:
{generated_answer}

Reference Answer:
{test.reference_answer}

Please evaluate the generated answer on three dimensions:
1. Accuracy: How factually correct is it compared to the reference answer?
2. Completeness: How thoroughly does it address all aspects of the question?
3. Relevance: How well does it directly answer the specific question asked?

Provide detailed feedback and scores from 1 (very poor) to 5 (ideal) for each dimension. If the answer is wrong, then the accuracy score must be 1.""",
        },
    ]
    
    # Call LLM judge with structured outputs (OpenAI native)
    judge_response = client.beta.chat.completions.parse(
        model=MODEL, 
        messages=judge_messages, 
        response_format=AnswerEval
    )
    answer_eval = judge_response.choices[0].message.parsed
    
    return answer_eval, generated_answer, retrieved_docs

def run_evaluation(answer_sample_size=10, config_name=""):
    """Run comprehensive evaluation"""
    print("=" * 80)
    if config_name:
        print(f"RAG SYSTEM EVALUATION - {config_name}")
    else:
        print("RAG SYSTEM EVALUATION")
    print("=" * 80)
    
    # Load tests
    print("\nLoading test questions...")
    tests = load_tests()
    print(f"   ✓ Loaded {len(tests)} test questions")
    print(f"   ✓ Categories: {set(t.category for t in tests)}")
    
    # Run retrieval evaluation
    print("\nRunning retrieval evaluation...")
    print("-" * 80)
    
    retrieval_results = []
    
    for i, test in enumerate(tests):
        print(f"[{i+1}/{len(tests)}] {test.question[:60]}...", end='')
        try:
            result = evaluate_retrieval(test)
            retrieval_results.append({
                'question': test.question,
                'category': test.category,
                'mrr': result.mrr,
                'ndcg': result.ndcg,
                'keywords_found': result.keywords_found,
                'total_keywords': result.total_keywords,
                'coverage': result.keyword_coverage
            })
            print(f" ✓ MRR={result.mrr:.3f}")
        except Exception as e:
            print(f" ✗ Error: {e}")
            retrieval_results.append({
                'question': test.question,
                'category': test.category,
                'mrr': 0.0,
                'ndcg': 0.0,
                'keywords_found': 0,
                'total_keywords': len(test.keywords),
                'coverage': 0.0
            })
    
    print("-" * 80)
    print("✓ Retrieval evaluation complete")
    
    # Display retrieval results
    retrieval_df = pd.DataFrame(retrieval_results)
    print_retrieval_results(retrieval_df)
    
    # Run answer evaluation (sample)
    print("\nRunning answer quality evaluation (sample)...")
    print("-" * 80)
    
    random.seed(42)
    sample_size = min(answer_sample_size, len(tests))
    sample_tests = random.sample(tests, sample_size)
    answer_results = []
    
    for i, test in enumerate(sample_tests):
        print(f"[{i+1}/{sample_size}] {test.question[:60]}...", end='')
        try:
            eval_result, generated_answer, _ = evaluate_answer(test)
            answer_results.append({
                'question': test.question,
                'category': test.category,
                'generated_answer': generated_answer,
                'reference_answer': test.reference_answer,
                'accuracy': eval_result.accuracy,
                'completeness': eval_result.completeness,
                'relevance': eval_result.relevance,
                'feedback': eval_result.feedback
            })
            print(f" ✓ Acc={eval_result.accuracy:.1f}")
        except Exception as e:
            print(f" ✗ Error: {e}")
            continue
    
    print("-" * 80)
    print("✓ Answer evaluation complete")
    
    # Display answer results
    if answer_results:
        answer_df = pd.DataFrame(answer_results)
        print_answer_results(answer_df)
    
    # Save results
    save_evaluation_results(retrieval_df, retrieval_results, answer_results)
    
    return retrieval_results, answer_results

def print_retrieval_results(retrieval_df):
    """Print retrieval evaluation results"""
    print("\n" + "=" * 80)
    print("RETRIEVAL EVALUATION RESULTS")
    print("=" * 80)
    
    print(f"\nOverall Metrics:")
    print(f"  Average MRR:      {retrieval_df['mrr'].mean():.4f}")
    print(f"  Average nDCG:     {retrieval_df['ndcg'].mean():.4f}")
    print(f"  Average Coverage: {retrieval_df['coverage'].mean():.1f}%")
    
    print(f"\nBy Category:")
    category_stats = retrieval_df.groupby('category').agg({
        'mrr': 'mean',
        'ndcg': 'mean',
        'coverage': 'mean'
    }).round(4)
    print(category_stats)
    
    print(f"\nWorst 5 Performing Questions (by MRR):")
    worst = retrieval_df.nsmallest(5, 'mrr')[['question', 'category', 'mrr', 'coverage']]
    print(worst.to_string(index=False))

def print_answer_results(answer_df):
    """Print answer quality evaluation results"""
    print("\n" + "=" * 80)
    print("ANSWER QUALITY EVALUATION RESULTS")
    print("=" * 80)
    
    print(f"\nOverall Metrics (sample of {len(answer_df)} questions):")
    print(f"  Average Accuracy:     {answer_df['accuracy'].mean():.2f}/5.00")
    print(f"  Average Completeness: {answer_df['completeness'].mean():.2f}/5.00")
    print(f"  Average Relevance:    {answer_df['relevance'].mean():.2f}/5.00")
    
    print(f"\nSample Results:")
    for i, row in answer_df.head(3).iterrows():
        print(f"\n--- Question {i+1} ---")
        print(f"Q: {row['question']}")
        print(f"A: {row['generated_answer'][:200]}...")
        print(f"Scores: Accuracy={row['accuracy']:.1f}, Completeness={row['completeness']:.1f}, Relevance={row['relevance']:.1f}")
        print(f"Feedback: {row['feedback']}")

def save_evaluation_results(retrieval_df, retrieval_results, answer_results):
    """Save evaluation results to JSON"""
    category_stats = retrieval_df.groupby('category').agg({
        'mrr': 'mean',
        'ndcg': 'mean',
        'coverage': 'mean'
    }).round(4)
    
    evaluation_results = {
        'retrieval': {
            'avg_mrr': float(retrieval_df['mrr'].mean()),
            'avg_ndcg': float(retrieval_df['ndcg'].mean()),
            'avg_coverage': float(retrieval_df['coverage'].mean()),
            'by_category': category_stats.to_dict(),
            'all_results': retrieval_results
        }
    }
    
    if answer_results:
        answer_df = pd.DataFrame(answer_results)
        evaluation_results['answer_quality'] = {
            'avg_accuracy': float(answer_df['accuracy'].mean()),
            'avg_completeness': float(answer_df['completeness'].mean()),
            'avg_relevance': float(answer_df['relevance'].mean()),
            'sample_results': answer_results
        }
    
    results_path = SCRIPT_DIR / 'evaluation_results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(evaluation_results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✓ Results saved to {results_path}")
    print("=" * 80)
    print("\nEvaluation complete!")
    print(f"  Retrieval MRR:  {evaluation_results['retrieval']['avg_mrr']:.4f}")
    print(f"  Retrieval nDCG: {evaluation_results['retrieval']['avg_ndcg']:.4f}")
    if 'answer_quality' in evaluation_results:
        print(f"  Answer Accuracy: {evaluation_results['answer_quality']['avg_accuracy']:.2f}/5.00")
    print("=" * 80)
    
    # Return results for comparison mode
    return retrieval_results, answer_results if answer_results else []

def compare_rag_configurations(answer_sample_size=10):
    """Compare all 4 RAG configurations"""
    import answer
    
    configs = [
        ("Baseline (neither)", False, False),
        ("Query Expansion only", True, False),
        ("Hybrid Search only", False, True),
        ("Both enabled", True, True),
    ]
    
    all_results = []
    
    for i, (config_name, use_qe, use_hs) in enumerate(configs):
        print(f"\n\n{'='*80}")
        print(f"CONFIGURATION {i+1}/4: {config_name}")
        print(f"  Query Expansion: {use_qe}")
        print(f"  Hybrid Search: {use_hs}")
        print(f"{'='*80}\n")
        
        # Set configuration flags
        answer.USE_QUERY_EXPANSION = use_qe
        answer.USE_HYBRID_SEARCH = use_hs
        
        # Clear cached components to force re-initialization
        answer.vectorstore = None
        answer.retriever = None
        answer._bm25 = None
        answer._bm25_docs = None
        
        # Run evaluation
        retrieval_results, answer_results = run_evaluation(answer_sample_size, config_name)
        
        # Calculate metrics
        retrieval_df = pd.DataFrame(retrieval_results)
        result = {
            'config': config_name,
            'query_expansion': use_qe,
            'hybrid_search': use_hs,
            'mrr': float(retrieval_df['mrr'].mean()),
            'ndcg': float(retrieval_df['ndcg'].mean()),
            'coverage': float(retrieval_df['coverage'].mean()),
        }
        
        if answer_results:
            answer_df = pd.DataFrame(answer_results)
            result.update({
                'accuracy': float(answer_df['accuracy'].mean()),
                'completeness': float(answer_df['completeness'].mean()),
                'relevance': float(answer_df['relevance'].mean()),
            })
        
        all_results.append(result)
    
    # Print comparison table
    print("\n" + "="*80)
    print("RAG TECHNIQUES COMPARISON")
    print("="*80)
    print(f"\n{'Configuration':<25} {'MRR':<8} {'nDCG':<8} {'Cover%':<8} {'Accur':<7} {'Compl':<7} {'Relev':<7}")
    print("-"*80)
    
    for r in all_results:
        print(f"{r['config']:<25} {r['mrr']:<8.4f} {r['ndcg']:<8.4f} {r['coverage']:<8.1f} "
              f"{r.get('accuracy', 0):<7.2f} {r.get('completeness', 0):<7.2f} {r.get('relevance', 0):<7.2f}")
    
    # Find best configuration
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    best_mrr = max(all_results, key=lambda x: x['mrr'])
    best_ndcg = max(all_results, key=lambda x: x['ndcg'])
    best_accuracy = max(all_results, key=lambda x: x.get('accuracy', 0))
    
    print(f"\nBest MRR: {best_mrr['config']} ({best_mrr['mrr']:.4f})")
    print(f"Best nDCG: {best_ndcg['config']} ({best_ndcg['ndcg']:.4f})")
    if best_accuracy.get('accuracy'):
        print(f"Best Accuracy: {best_accuracy['config']} ({best_accuracy['accuracy']:.2f}/5.0)")
    
    # Save detailed results
    results_path = SCRIPT_DIR / 'rag_techniques_comparison.json'
    with open(results_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✓ Detailed results saved to {results_path}")
    print("="*80)
    
    return all_results

def parse_list_arg(arg_str):
    """Parse comma-separated list argument"""
    return [int(x.strip()) for x in arg_str.split(',')]

def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive evaluation and hyperparameter tuning for Persona RAG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run everything
  python evaluate.py --all
  
  # Only hyperparameter tuning
  python evaluate.py --tune
  
  # Only evaluation
  python evaluate.py --eval
  
  # Compare all 4 RAG configurations (baseline, query expansion, hybrid, both)
  python evaluate.py --compare-rag
  
  # Test with query expansion enabled
  python evaluate.py --eval --query-expansion
  
  # Test with hybrid search enabled
  python evaluate.py --eval --hybrid-search
  
  # Test with both enabled
  python evaluate.py --eval --query-expansion --hybrid-search
  
  # Custom hyperparameter ranges
  python evaluate.py --tune --chunk-sizes 500,1000,1500 --k-values 3,5,7,9
  
  # Custom evaluation sample size
  python evaluate.py --eval --answer-sample-size 15
        """
    )
    
    # Mode selection
    parser.add_argument('--all', action='store_true', help='Run both tuning and evaluation')
    parser.add_argument('--tune', action='store_true', help='Run hyperparameter tuning only')
    parser.add_argument('--eval', action='store_true', help='Run evaluation only')
    
    # Hyperparameter tuning options
    parser.add_argument('--chunk-sizes', type=str, default='500,750,1000,1250,1500,1750,2000',
                        help='Comma-separated list of chunk sizes to test (default: 500,750,1000,1250,1500,1750,2000)')
    parser.add_argument('--k-values', type=str, default='3,5,7,9,11,13,15,20',
                        help='Comma-separated list of K values to test (default: 3,5,7,9,11,13,15,20)')
    parser.add_argument('--tune-sample-size', type=int, default=20,
                        help='Number of test questions to sample for tuning (default: 20)')
    
    # Evaluation options
    parser.add_argument('--answer-sample-size', type=int, default=10,
                        help='Number of questions to evaluate for answer quality (default: 10)')
    
    # RAG technique options
    parser.add_argument('--query-expansion', action='store_true',
                        help='Enable query expansion (generates alternative phrasings)')
    parser.add_argument('--hybrid-search', action='store_true',
                        help='Enable hybrid search (BM25 + semantic search)')
    parser.add_argument('--compare-rag', action='store_true',
                        help='Compare all 4 RAG configurations (baseline, query expansion, hybrid, both)')
    
    args = parser.parse_args()
    
    # If no mode specified, show help
    if not (args.all or args.tune or args.eval or args.compare_rag):
        parser.print_help()
        sys.exit(1)
    
    # Parse list arguments
    chunk_sizes = parse_list_arg(args.chunk_sizes)
    k_values = parse_list_arg(args.k_values)
    
    # Run requested operations
    if args.all or args.tune:
        run_hyperparameter_tuning(chunk_sizes, k_values, args.tune_sample_size)
    
    # Handle RAG configuration comparison mode
    if args.compare_rag:
        if args.all or args.tune:
            print("\n\n") 
        compare_rag_configurations(args.answer_sample_size)
    elif args.all or args.eval:
        # Set RAG configuration flags if specified
        if args.query_expansion or args.hybrid_search:
            import answer
            answer.USE_QUERY_EXPANSION = args.query_expansion
            answer.USE_HYBRID_SEARCH = args.hybrid_search
            print("\n" + "="*80)
            print("RAG CONFIGURATION")
            print("="*80)
            print(f"  Query Expansion: {args.query_expansion}")
            print(f"  Hybrid Search: {args.hybrid_search}")
            print("="*80 + "\n")
        
        if args.all or args.tune:
            print("\n\n")
        run_evaluation(args.answer_sample_size)

if __name__ == "__main__":
    main()

