#!/usr/bin/env python3
"""
Simple AI Tool Test for Finance Copilot
Tests AI tools directly and provides basic validation
"""

import sys
import os
import json
import time
from typing import Dict, List

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agent import FinanceCopilotAgent
from config import Config

class SimpleAITester:
    def __init__(self):
        """Initialize the simple AI tester"""
        self.config = Config()
        self.ai_agent = FinanceCopilotAgent()
        
        # Test cases
        self.test_cases = [
            {
                "id": "stock_price_aapl",
                "question": "What's the current price of AAPL?",
                "tool": "get_stock_price",
                "expected_keywords": ["price", "AAPL", "change", "volume"],
                "description": "Stock price for Apple"
            },
            {
                "id": "stock_price_googl",
                "question": "Get the stock price for GOOGL",
                "tool": "get_stock_price", 
                "expected_keywords": ["price", "GOOGL", "change", "volume"],
                "description": "Stock price for Google"
            },
            {
                "id": "fundamentals_msft",
                "question": "Show me the fundamentals for MSFT",
                "tool": "get_stock_fundamentals",
                "expected_keywords": ["PE", "ratio", "market cap", "MSFT"],
                "description": "Fundamentals for Microsoft"
            },
            {
                "id": "portfolio_status",
                "question": "What's in my portfolio?",
                "tool": "get_portfolio",
                "expected_keywords": ["portfolio", "symbol", "shares"],
                "description": "Portfolio holdings"
            },
            {
                "id": "market_overview",
                "question": "Give me a market summary",
                "tool": "get_market_summary",
                "expected_keywords": ["market", "indices", "summary"],
                "description": "Market overview"
            },
            {
                "id": "crypto_bitcoin",
                "question": "What's the current price of Bitcoin?",
                "tool": "get_crypto_price",
                "expected_keywords": ["price", "Bitcoin", "BTC", "change"],
                "description": "Bitcoin price"
            }
        ]
    
    def test_tool_directly(self, tool_name: str, params: Dict = None) -> Dict:
        """Test a tool directly without going through the AI agent"""
        try:
            print(f"   🔧 Testing tool directly: {tool_name}")
            
            # Map tool names to actual methods
            tool_methods = {
                "get_stock_price": lambda: self.ai_agent._get_stock_price("AAPL"),
                "get_crypto_price": lambda: self.ai_agent._get_crypto_price("BTC-USD"),
                "get_stock_fundamentals": lambda: self.ai_agent._get_stock_fundamentals("AAPL"),
                "get_portfolio": lambda: self.ai_agent._get_portfolio(),
                "get_market_summary": lambda: self.ai_agent._get_market_summary(),
            }
            
            if tool_name in tool_methods:
                result = tool_methods[tool_name]()
                return {"success": True, "result": result, "error": None}
            else:
                return {"success": False, "result": None, "error": f"Tool {tool_name} not found"}
                
        except Exception as e:
            return {"success": False, "result": None, "error": str(e)}
    
    def validate_response_basic(self, response: str, expected_keywords: List[str]) -> Dict:
        """Basic validation of response content"""
        if not response:
            return {"score": 1, "issues": ["Empty response"], "status": "FAIL"}
        
        response_lower = response.lower()
        issues = []
        score = 10
        
        # Check for error messages
        if "error" in response_lower:
            issues.append("Response contains error message")
            score -= 5
        
        # Check for expected keywords
        for keyword in expected_keywords:
            if keyword.lower() not in response_lower:
                issues.append(f"Missing keyword: {keyword}")
                score -= 1
        
        # Check response length
        if len(response) < 50:
            issues.append("Response too short")
            score -= 2
        
        # Ensure score doesn't go below 1
        score = max(1, score)
        
        # Determine status
        if score >= 9:
            status = "PASS"
        elif score >= 7:
            status = "WARNING"
        else:
            status = "FAIL"
        
        return {
            "score": score,
            "issues": issues,
            "status": status,
            "meets_threshold": score >= 9
        }
    
    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case"""
        print(f"\n🧪 Running Test: {test_case['id']}")
        print(f"   📋 Description: {test_case['description']}")
        print(f"   ❓ Question: {test_case['question']}")
        print(f"   🎯 Expected Tool: {test_case['tool']}")
        
        # Test 1: Direct tool execution
        print(f"   🔧 Testing tool directly...")
        direct_result = self.test_tool_directly(test_case['tool'])
        
        if not direct_result['success']:
            print(f"   ❌ Tool test failed: {direct_result['error']}")
            return {
                "test_id": test_case['id'],
                "question": test_case['question'],
                "tool": test_case['tool'],
                "direct_tool_result": direct_result,
                "ai_response": "N/A",
                "ai_response_time": 0,
                "validation": {"score": 1, "issues": ["Tool failed"], "status": "FAIL", "meets_threshold": False},
                "overall_status": "FAIL"
            }
        
        print(f"   ✅ Tool working directly")
        
        # Test 2: AI agent response
        print(f"   🤖 Testing through AI agent...")
        start_time = time.time()
        
        try:
            ai_response = self.ai_agent.process_query(test_case['question'])
            ai_response_time = time.time() - start_time
            print(f"   ✅ AI response received ({len(ai_response)} characters)")
        except Exception as e:
            ai_response = f"Error: {str(e)}"
            ai_response_time = 0
            print(f"   ❌ AI response failed: {e}")
        
        # Validate AI response
        validation = self.validate_response_basic(ai_response, test_case['expected_keywords'])
        
        # Determine overall status
        if validation['meets_threshold'] and direct_result['success']:
            overall_status = "PASS"
        elif direct_result['success'] and validation['score'] >= 7:
            overall_status = "WARNING"
        else:
            overall_status = "FAIL"
        
        result = {
            "test_id": test_case['id'],
            "question": test_case['question'],
            "tool": test_case['tool'],
            "direct_tool_result": direct_result,
            "ai_response": ai_response,
            "ai_response_time": round(ai_response_time, 2),
            "validation": validation,
            "overall_status": overall_status
        }
        
        print(f"   ⏱️  AI Response Time: {ai_response_time:.2f}s")
        print(f"   🎯 Validation Score: {validation['score']}/10")
        print(f"   📊 Meets Threshold (9+): {'✅ YES' if validation['meets_threshold'] else '❌ NO'}")
        print(f"   📝 Overall Status: {overall_status}")
        
        if validation['issues']:
            print(f"   ⚠️  Issues: {', '.join(validation['issues'])}")
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run all test cases"""
        print("🚀 Finance Copilot - Simple AI Tool Test Suite")
        print("=" * 60)
        print("🎯 Testing AI tools directly and through AI agent")
        print("📊 Threshold for good response: 9/10")
        print("=" * 60)
        
        results = []
        
        for test_case in self.test_cases:
            try:
                result = self.run_test_case(test_case)
                results.append(result)
                
                # Add delay between tests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
                error_result = {
                    "test_id": test_case['id'],
                    "question": test_case['question'],
                    "tool": test_case['tool'],
                    "direct_tool_result": {"success": False, "error": str(e)},
                    "ai_response": f"Test failed: {str(e)}",
                    "ai_response_time": 0,
                    "validation": {"score": 1, "issues": [f"Test failed: {e}"], "status": "FAIL", "meets_threshold": False},
                    "overall_status": "ERROR"
                }
                results.append(error_result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate test report"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['overall_status'] == "PASS")
        warning_tests = sum(1 for r in results if r['overall_status'] == "WARNING")
        failed_tests = total_tests - passed_tests - warning_tests
        
        # Calculate average scores
        scores = [r['validation']['score'] for r in results if r['validation']['score'] > 0]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Calculate average response times
        response_times = [r['ai_response_time'] for r in results if r['ai_response_time'] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = f"""
📊 SIMPLE AI TOOL TEST REPORT
{'='*60}

🎯 TEST SUMMARY:
   Total Tests: {total_tests}
   ✅ Passed: {passed_tests}
   ⚠️  Warning: {warning_tests}
   ❌ Failed: {failed_tests}
   📊 Success Rate: {(passed_tests/total_tests*100):.1f}%

📈 PERFORMANCE METRICS:
   🎯 Average Validation Score: {avg_score:.1f}/10
   ⏱️  Average AI Response Time: {avg_response_time:.2f}s

🔍 DETAILED RESULTS:
"""
        
        for result in results:
            report += f"""
🧪 {result['test_id']}: {result['overall_status']}
   ❓ Question: {result['question']}
   🎯 Tool: {result['tool']}
   ⏱️  AI Response Time: {result['ai_response_time']}s
   🎯 Validation Score: {result['validation']['score']}/10
   📝 AI Response Preview: {result['ai_response'][:100]}...
   🔧 Direct Tool: {'✅ Working' if result['direct_tool_result']['success'] else '❌ Failed'}
"""
        
        # Add recommendations
        if failed_tests > 0:
            report += f"""
⚠️  RECOMMENDATIONS:
   - {failed_tests} tests failed completely
   - {warning_tests} tests have warnings
   - Check tool integration and API availability
   - Review error messages for common patterns
"""
        elif warning_tests > 0:
            report += f"""
⚠️  RECOMMENDATIONS:
   - {warning_tests} tests have warnings but tools are working
   - Review AI responses for quality improvements
   - Consider adjusting validation criteria
"""
        else:
            report += f"""
🎉 EXCELLENT RESULTS:
   - All tests passed!
   - AI tools are working correctly
   - Response quality meets expectations
"""
        
        return report
    
    def save_results(self, results: List[Dict], filename: str = "simple_ai_test_results.json"):
        """Save test results to JSON file"""
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    """Main test runner"""
    try:
        # Initialize tester
        tester = SimpleAITester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_report(results)
        print(report)
        
        # Save results
        tester.save_results(results)
        
        # Summary
        passed = sum(1 for r in results if r['overall_status'] == "PASS")
        total = len(results)
        
        print(f"\n🎯 FINAL SUMMARY:")
        print(f"   Tests Passed: {passed}/{total}")
        print(f"   Success Rate: {(passed/total*100):.1f}%")
        
        if passed == total:
            print("🎉 All tests passed! AI tools are working correctly.")
        else:
            print("⚠️  Some tests failed. Check the detailed report above.")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
