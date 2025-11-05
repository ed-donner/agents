import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.test_helpers import run_all_tests as test_helpers
from tests.test_rag_system import run_all_tests as test_rag
from tests.test_evaluation import run_all_tests as test_evaluation


def main():
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUITE FOR ADVANCED DIGITAL TWIN")
    print("="*80)
    
    start_time = time.time()
    
    test_suites = [
        ("Helper Functions", test_helpers),
        ("RAG System", test_rag),
        ("Evaluation Framework", test_evaluation)
    ]
    
    results = []
    
    for suite_name, test_func in test_suites:
        print(f"\n{'='*80}")
        print(f"Running: {suite_name}")
        print('='*80)
        result = test_func()
        results.append((suite_name, result))
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("FINAL TEST RESULTS")
    print("="*80)
    
    for suite_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{suite_name:30s} : {status}")
    
    total_passed = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    print("\n" + "="*80)
    print(f"Overall: {total_passed}/{total_tests} test suites passed")
    print(f"Time: {elapsed:.2f} seconds")
    print("="*80)
    
    if all(result for _, result in results):
        print("\n🎉 ALL TESTS PASSED! System is working correctly.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

