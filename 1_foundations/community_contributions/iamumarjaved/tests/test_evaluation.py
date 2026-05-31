import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent.parent.parent.parent / ".env", override=True)

from evaluation import RAGEvaluator, create_test_cases
from rag_system import RAGSystem


def test_mrr_calculation():
    print("\n" + "="*60)
    print("TEST: Mean Reciprocal Rank")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evaluator = RAGEvaluator(client)
        
        retrieved = ["doc3", "doc1", "doc2"]
        relevant = ["doc1"]
        mrr = evaluator.mean_reciprocal_rank(retrieved, relevant)
        
        expected = 1.0 / 2
        assert abs(mrr - expected) < 0.001, f"MRR should be {expected}, got {mrr}"
        
        print(f"✓ MRR calculation correct: {mrr}")
        print("✅ MRR test PASSED")
        return True
    except Exception as e:
        print(f"❌ MRR test FAILED: {e}")
        return False


def test_ndcg_calculation():
    print("\n" + "="*60)
    print("TEST: Normalized DCG")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evaluator = RAGEvaluator(client)
        
        retrieved = ["doc1", "doc2", "doc3"]
        relevance_scores = {"doc1": 5, "doc2": 3, "doc3": 1}
        ndcg = evaluator.ndcg_at_k(retrieved, relevance_scores, k=3)
        
        assert 0 <= ndcg <= 1, f"nDCG should be between 0 and 1, got {ndcg}"
        
        print(f"✓ nDCG calculation: {ndcg:.4f}")
        print("✅ nDCG test PASSED")
        return True
    except Exception as e:
        print(f"❌ nDCG test FAILED: {e}")
        return False


def test_precision_recall():
    print("\n" + "="*60)
    print("TEST: Precision and Recall")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evaluator = RAGEvaluator(client)
        
        retrieved = ["doc1", "doc2", "doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc3", "doc6"]
        
        precision = evaluator.precision_at_k(retrieved, relevant, k=5)
        recall = evaluator.recall_at_k(retrieved, relevant, k=5)
        
        expected_precision = 2 / 5
        expected_recall = 2 / 3
        
        assert abs(precision - expected_precision) < 0.001, f"Precision should be {expected_precision}"
        assert abs(recall - expected_recall) < 0.001, f"Recall should be {expected_recall}"
        
        print(f"✓ Precision@5: {precision:.4f}")
        print(f"✓ Recall@5: {recall:.4f}")
        print("✅ Precision/Recall test PASSED")
        return True
    except Exception as e:
        print(f"❌ Precision/Recall test FAILED: {e}")
        return False


def test_llm_as_judge():
    print("\n" + "="*60)
    print("TEST: LLM-as-Judge")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evaluator = RAGEvaluator(client)
        
        query = "What programming languages do you know?"
        answer = "I am proficient in Python, JavaScript, and SQL."
        
        result = evaluator.llm_as_judge_answer(query, answer)
        
        assert "accuracy" in result, "Should have accuracy score"
        assert "completeness" in result, "Should have completeness score"
        assert "relevance" in result, "Should have relevance score"
        assert "coherence" in result, "Should have coherence score"
        assert "overall_score" in result, "Should have overall score"
        assert "feedback" in result, "Should have feedback"
        
        print(f"✓ Accuracy: {result['accuracy']}/5")
        print(f"✓ Completeness: {result['completeness']}/5")
        print(f"✓ Relevance: {result['relevance']}/5")
        print(f"✓ Coherence: {result['coherence']}/5")
        print(f"✓ Overall: {result['overall_score']}/5")
        print(f"✓ Feedback: {result['feedback'][:50]}...")
        print("✅ LLM-as-Judge test PASSED")
        return True
    except Exception as e:
        print(f"❌ LLM-as-Judge test FAILED: {e}")
        return False


def test_create_test_cases():
    print("\n" + "="*60)
    print("TEST: Test Case Creation")
    print("="*60)
    
    try:
        queries = [
            ("What is your experience?", "Expected answer 1"),
            ("What skills do you have?", "Expected answer 2")
        ]
        
        test_cases = create_test_cases(queries)
        
        assert isinstance(test_cases, list), "Should return a list"
        assert len(test_cases) == 2, "Should create 2 test cases"
        assert "query" in test_cases[0], "Should have query field"
        assert "ground_truth" in test_cases[0], "Should have ground_truth field"
        
        print(f"✓ Created {len(test_cases)} test cases")
        print("✅ Test case creation test PASSED")
        return True
    except Exception as e:
        print(f"❌ Test case creation test FAILED: {e}")
        return False


def test_rag_evaluation():
    print("\n" + "="*60)
    print("TEST: RAG System Evaluation")
    print("="*60)
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        evaluator = RAGEvaluator(client)
        rag_system = RAGSystem(client, data_dir="data/test_eval")
        
        test_docs = {
            "summary": "Expert Python developer with 5 years experience",
            "projects": "Built ML systems and web applications"
        }
        
        rag_system.load_knowledge_base(test_docs, chunk_size=15, overlap=3)
        
        test_cases = create_test_cases([("What programming experience do you have?", "Python development")])
        
        system_prompt = "Answer questions about professional background."
        results = evaluator.evaluate_rag_system(test_cases, rag_system, system_prompt, method="hybrid")
        
        assert len(results) > 0, "Should produce evaluation results"
        assert "query" in results.columns, "Should have query column"
        assert "overall_score" in results.columns, "Should have overall_score column"
        
        print(f"✓ Evaluated {len(results)} queries")
        print(f"✓ Average score: {results['overall_score'].mean():.2f}/5")
        print("✅ RAG evaluation test PASSED")
        return True
    except Exception as e:
        print(f"❌ RAG evaluation test FAILED: {e}")
        return False


def run_all_tests():
    print("\n" + "="*70)
    print("RUNNING EVALUATION TESTS")
    print("="*70)
    
    tests = [
        test_mrr_calculation,
        test_ndcg_calculation,
        test_precision_recall,
        test_llm_as_judge,
        test_create_test_cases,
        test_rag_evaluation
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "="*70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("="*70)
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

