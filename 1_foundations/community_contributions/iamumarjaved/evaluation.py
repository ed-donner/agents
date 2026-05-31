import json
import numpy as np
from typing import List, Dict
from pathlib import Path
import pandas as pd
from datetime import datetime


class RAGEvaluator:
    
    def __init__(self, openai_client):
        self.client = openai_client
        
    def mean_reciprocal_rank(self, retrieved_docs: List[str], relevant_docs: List[str]) -> float:
        for i, doc_id in enumerate(retrieved_docs, 1):
            if doc_id in relevant_docs:
                return 1.0 / i
        return 0.0
    
    def dcg_at_k(self, relevances: List[float], k: int = None) -> float:
        if k is not None:
            relevances = relevances[:k]
        if not relevances:
            return 0.0
        return relevances[0] + sum(rel / np.log2(i + 1) for i, rel in enumerate(relevances[1:], 2))
    
    def ndcg_at_k(self, retrieved_docs: List[str], relevance_scores: Dict[str, float], k: int = 5) -> float:
        retrieved_relevances = [relevance_scores.get(doc_id, 0.0) for doc_id in retrieved_docs[:k]]
        dcg = self.dcg_at_k(retrieved_relevances, k)
        ideal_relevances = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = self.dcg_at_k(ideal_relevances, k)
        if idcg == 0:
            return 0.0
        return dcg / idcg
    
    def precision_at_k(self, retrieved_docs: List[str], relevant_docs: List[str], k: int = 5) -> float:
        retrieved_k = retrieved_docs[:k]
        relevant_count = sum(1 for doc in retrieved_k if doc in relevant_docs)
        return relevant_count / k if k > 0 else 0.0
    
    def recall_at_k(self, retrieved_docs: List[str], relevant_docs: List[str], k: int = 5) -> float:
        if not relevant_docs:
            return 0.0
        retrieved_k = retrieved_docs[:k]
        relevant_count = sum(1 for doc in retrieved_k if doc in relevant_docs)
        return relevant_count / len(relevant_docs)
    
    def llm_as_judge_relevance(self, query: str, document: str, context: str = "") -> Dict:
        prompt = f"""You are evaluating the relevance of a document to a user query.

Context: {context}
Query: {query}
Document: {document}

Rate the relevance of this document to the query on a scale of 0-5:
- 0: Completely irrelevant
- 1: Minimally relevant
- 2: Somewhat relevant
- 3: Moderately relevant
- 4: Very relevant
- 5: Perfectly relevant

Respond with ONLY a JSON object in this format:
{{"relevance_score": <number>, "explanation": "<brief explanation>"}}"""
        
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"LLM judge failed: {e}")
            return {"relevance_score": 0, "explanation": "Error in evaluation"}
    
    def llm_as_judge_answer(self, query: str, answer: str, ground_truth: str = None, context: List[str] = None) -> Dict:
        prompt = f"""You are evaluating the quality of an AI assistant's answer.

Query: {query}
Answer: {answer}
"""
        if ground_truth:
            prompt += f"\nGround Truth:\n{ground_truth}\n"
        if context:
            prompt += f"\nAvailable Context:\n" + "\n---\n".join(context[:3])
        
        prompt += """
Rate the answer on these dimensions (0-5 scale each):
- Accuracy: How factually correct is the answer?
- Completeness: Does it fully address the query?
- Relevance: Is the answer focused on the question?
- Coherence: Is it well-structured and clear?

Respond with ONLY a JSON object:
{
  "accuracy": <number>,
  "completeness": <number>,
  "relevance": <number>,
  "coherence": <number>,
  "overall_score": <number>,
  "feedback": "<brief explanation>"
}"""
        
        try:
            response = self.client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], temperature=0.3)
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"LLM judge failed: {e}")
            return {"accuracy": 0, "completeness": 0, "relevance": 0, "coherence": 0, "overall_score": 0, "feedback": f"Error: {e}"}
    
    def evaluate_retrieval(self, test_cases: List[Dict], retriever, method: str = "hybrid_rerank", k: int = 5) -> pd.DataFrame:
        results = []
        for test_case in test_cases:
            query = test_case["query"]
            relevant_docs = test_case.get("relevant_docs", [])
            relevance_scores = test_case.get("relevance_scores", {})
            
            retrieved = retriever.retrieve(query, method=method, top_k=k)
            retrieved_ids = [doc["id"] for doc in retrieved]
            
            mrr = self.mean_reciprocal_rank(retrieved_ids, relevant_docs)
            ndcg = self.ndcg_at_k(retrieved_ids, relevance_scores, k)
            precision = self.precision_at_k(retrieved_ids, relevant_docs, k)
            recall = self.recall_at_k(retrieved_ids, relevant_docs, k)
            
            results.append({
                "query": query,
                "method": method,
                "mrr": mrr,
                "ndcg@k": ndcg,
                "precision@k": precision,
                "recall@k": recall,
                "num_retrieved": len(retrieved_ids)
            })
        return pd.DataFrame(results)
    
    def evaluate_rag_system(self, test_cases: List[Dict], rag_system, system_prompt: str, method: str = "hybrid_rerank") -> pd.DataFrame:
        results = []
        for test_case in test_cases:
            query = test_case["query"]
            ground_truth = test_case.get("ground_truth")
            
            response = rag_system.query(query, system_prompt, method=method)
            context_texts = [doc["text"] for doc in response["context"]]
            judge_result = self.llm_as_judge_answer(query, response["answer"], ground_truth, context_texts)
            
            results.append({
                "query": query,
                "method": method,
                "answer": response["answer"],
                "num_context_docs": len(response["context"]),
                **judge_result
            })
        return pd.DataFrame(results)
    
    def compare_rag_methods(self, test_cases: List[Dict], rag_system, system_prompt: str, methods: List[str] = None) -> pd.DataFrame:
        if methods is None:
            methods = ["bm25", "semantic", "hybrid", "hybrid_rerank"]
        
        all_results = []
        for method in methods:
            print(f"\nEvaluating method: {method}")
            method_results = self.evaluate_rag_system(test_cases, rag_system, system_prompt, method)
            all_results.append(method_results)
        
        combined = pd.concat(all_results, ignore_index=True)
        return combined
    
    def save_evaluation_report(self, results: pd.DataFrame, output_dir: str = "evaluations", name: str = "evaluation"):
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = output_path / f"{name}_{timestamp}.csv"
        results.to_csv(csv_path, index=False)
        print(f"Saved CSV to {csv_path}")
        
        summary = results.groupby("method").agg({
            "overall_score": ["mean", "std"],
            "accuracy": "mean",
            "completeness": "mean",
            "relevance": "mean",
            "coherence": "mean"
        }).round(3)
        
        summary_path = output_path / f"{name}_summary_{timestamp}.txt"
        with open(summary_path, "w") as f:
            f.write("RAG Evaluation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(summary.to_string())
            f.write("\n\n")
            f.write(f"Total queries evaluated: {len(results)}\n")
            f.write(f"Timestamp: {timestamp}\n")
        
        print(f"Saved summary to {summary_path}")
        return csv_path, summary_path


def create_test_cases(queries_and_answers: List[tuple]) -> List[Dict]:
    return [{"query": query, "ground_truth": answer} for query, answer in queries_and_answers]


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    
    from openai import OpenAI
    from helpers import get_config, load_all_documents
    from rag_system import RAGSystem
    
    print("RAG System Evaluation Demo")
    print("=" * 50)
    
    config = get_config()
    client = OpenAI(api_key=config["openai_api_key"])
    
    print("\nLoading documents...")
    app_dir = Path(__file__).parent
    documents = load_all_documents(str(app_dir / "me"))
    print(f"Loaded {len(documents)} documents")
    
    print("\nInitializing RAG system...")
    rag_system = RAGSystem(client, data_dir=str(app_dir / "data"))
    rag_system.load_knowledge_base(documents, chunk_size=500, overlap=50)
    print("RAG system ready")
    
    evaluator = RAGEvaluator(client)
    
    test_cases = create_test_cases([
        ("What is your background?", "Professional background and experience"),
        ("What technologies do you work with?", "List of technologies and tech stack"),
        ("What projects have you worked on?", "Description of projects and achievements")
    ])
    
    print(f"\nRunning evaluation with {len(test_cases)} test cases...")
    print("\nComparing RAG methods: BM25, Semantic, Hybrid, Hybrid+Rerank")
    
    system_prompt = f"You are an AI assistant representing {config['name']}. Answer questions based on the provided context."
    
    results = evaluator.compare_rag_methods(test_cases, rag_system, system_prompt)
    
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    
    summary = results.groupby("method").agg({
        "overall_score": ["mean", "std"],
        "accuracy": "mean",
        "completeness": "mean",
        "relevance": "mean",
        "coherence": "mean"
    }).round(3)
    
    print(summary)
    
    csv_path, summary_path = evaluator.save_evaluation_report(results, name="rag_comparison")
    
    print("\n" + "=" * 50)
    print(f"Detailed results saved to: {csv_path}")
    print(f"Summary saved to: {summary_path}")
    print("=" * 50)
