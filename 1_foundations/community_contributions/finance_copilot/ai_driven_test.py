#!/usr/bin/env python3
"""
AI-Driven Test Case with AI Validator Strategy
Tests AI tools and validates responses using AI rating (1-10 scale)
Threshold for good response: 9+
"""

import sys
import os
import json
import time
from typing import Dict, List, Tuple, Optional

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_agent import FinanceCopilotAgent
from config import Config

class AIDrivenTester:
    def __init__(self):
        """Initialize the AI-driven tester"""
        self.config = Config()
        self.ai_agent = FinanceCopilotAgent()
        
        # Test cases that should invoke specific tools
        self.test_cases = [
            {
                "id": "stock_price_1",
                "question": "What's the current price of AAPL?",
                "expected_tool": "get_stock_price",
                "expected_content": ["price", "AAPL", "change"],
                "description": "Basic stock price query for AAPL"
            },
            {
                "id": "stock_price_2", 
                "question": "Get the stock price for GOOGL",
                "expected_tool": "get_stock_price",
                "expected_content": ["price", "GOOGL", "change"],
                "description": "Stock price query for GOOGL"
            },
            {
                "id": "fundamentals_1",
                "question": "Show me the fundamentals for MSFT",
                "expected_tool": "get_stock_fundamentals", 
                "expected_content": ["PE ratio", "market cap", "MSFT"],
                "description": "Fundamentals query for Microsoft"
            },
            {
                "id": "portfolio_1",
                "question": "What's in my portfolio?",
                "expected_tool": "get_portfolio",
                "expected_content": ["portfolio", "symbols", "shares"],
                "description": "Portfolio status query"
            },
            {
                "id": "market_summary_1",
                "question": "Give me a market summary",
                "expected_tool": "get_market_summary",
                "expected_content": ["market", "indices", "summary"],
                "description": "Market overview query"
            },
            {
                "id": "crypto_1",
                "question": "What's the current price of Bitcoin?",
                "expected_tool": "get_crypto_price",
                "expected_content": ["price", "Bitcoin", "BTC"],
                "description": "Cryptocurrency price query"
            }
        ]
        
        # AI validation prompts
        self.validation_prompts = {
            "stock_price": """
Rate this AI response to a stock price query from 1-10:

Question: {question}
Response: {response}

Rating Criteria:
- 10: Perfect response with accurate price, change, volume, and helpful context
- 9: Excellent response with price data and some additional useful information
- 8: Good response with price data but missing some details
- 7: Adequate response with basic price information
- 6: Response has price data but with errors or poor formatting
- 5: Response mentions price but unclear or incomplete
- 4: Response doesn't directly answer the price question
- 3: Response is confusing or off-topic
- 2: Response is mostly incorrect
- 1: Response is completely wrong or error message

Expected: Stock price, change, percentage change, volume
Rate (1-10):""",
            
            "fundamentals": """
Rate this AI response to a fundamentals query from 1-10:

Question: {question}
Response: {response}

Rating Criteria:
- 10: Perfect response with PE ratio, market cap, debt/equity, ROE, and clear formatting
- 9: Excellent response with most key financial ratios and good formatting
- 8: Good response with several financial metrics but missing some key ones
- 7: Adequate response with basic financial information
- 6: Response has some financial data but unclear or incomplete
- 5: Response mentions fundamentals but doesn't provide specific metrics
- 4: Response doesn't directly answer the fundamentals question
- 3: Response is confusing or off-topic
- 2: Response is mostly incorrect
- 1: Response is completely wrong or error message

Expected: PE ratio, market cap, debt/equity, ROE, dividend yield
Rate (1-10):""",
            
            "portfolio": """
Rate this AI response to a portfolio query from 1-10:

Question: {question}
Response: {response}

Rating Criteria:
- 10: Perfect response showing portfolio holdings, shares, values, and clear formatting
- 9: Excellent response with portfolio data and good organization
- 8: Good response with portfolio information but missing some details
- 7: Adequate response with basic portfolio data
- 6: Response has portfolio info but unclear or incomplete
- 5: Response mentions portfolio but doesn't show specific holdings
- 4: Response doesn't directly answer the portfolio question
- 3: Response is confusing or off-topic
- 2: Response is mostly incorrect
- 1: Response is completely wrong or error message

Expected: List of holdings, symbols, shares, current values
Rate (1-10):""",
            
            "market_summary": """
Rate this AI response to a market summary query from 1-10:

Question: {question}
Response: {response}

Rating Criteria:
- 10: Perfect response with major indices, changes, and market overview
- 9: Excellent response with market data and good formatting
- 8: Good response with market information but missing some details
- 7: Adequate response with basic market data
- 6: Response has market info but unclear or incomplete
- 5: Response mentions market but doesn't provide specific data
- 4: Response doesn't directly answer the market question
- 3: Response is confusing or off-topic
- 2: Response is mostly incorrect
- 1: Response is completely wrong or error message

Expected: Major indices (S&P 500, Dow, NASDAQ), changes, market status
Rate (1-10):""",
            
            "crypto": """
Rate this AI response to a cryptocurrency query from 1-10:

Question: {question}
Response: {response}

Rating Criteria:
- 10: Perfect response with accurate price, change, volume, and helpful context
- 9: Excellent response with price data and some additional useful information
- 8: Good response with price data but missing some details
- 7: Adequate response with basic price information
- 6: Response has price data but with errors or poor formatting
- 5: Response mentions price but unclear or incomplete
- 4: Response doesn't directly answer the price question
- 3: Response is confusing or off-topic
- 2: Response is mostly incorrect
- 1: Response is completely wrong or error message

Expected: Cryptocurrency price, change, percentage change, volume
Rate (1-10):"""
        }
    
    def get_ai_response(self, question: str) -> str:
        """Get AI response for a question"""
        try:
            print(f"   🤖 Asking AI: {question}")
            response = self.ai_agent.process_query(question)
            print(f"   📝 Response received ({len(response)} characters)")
            return response
        except Exception as e:
            error_msg = f"Error getting AI response: {str(e)}"
            print(f"   ❌ {error_msg}")
            return error_msg
    
    def validate_response_with_ai(self, question: str, response: str, test_type: str) -> Tuple[int, str]:
        """Use AI to validate and rate the response (1-10 scale)"""
        try:
            if not self.ai_agent.llm:
                print("   ⚠️  OpenAI not configured, using basic validation")
                return self.basic_validation(response, test_type)
            
            # Get the appropriate validation prompt
            prompt_template = self.validation_prompts.get(test_type, self.validation_prompts["stock_price"])
            prompt = prompt_template.format(question=question, response=response)
            
            print(f"   🔍 Validating response with AI...")
            
            # Get AI validation
            validation_response = self.ai_agent.llm.invoke([{"role": "user", "content": prompt}])
            validation_content = validation_response.content if hasattr(validation_response, 'content') else str(validation_response)
            
            # Extract rating from response
            rating = self.extract_rating(validation_content)
            
            return rating, validation_content
            
        except Exception as e:
            print(f"   ⚠️  AI validation failed: {e}, using basic validation")
            return self.basic_validation(response, test_type)
    
    def basic_validation(self, response: str, test_type: str) -> Tuple[int, str]:
        """Basic validation when AI is not available"""
        if "error" in response.lower():
            return 2, "Basic validation: Response contains error message"
        
        if len(response) < 50:
            return 3, "Basic validation: Response too short"
        
        if test_type == "stock_price" and any(word in response.lower() for word in ["price", "stock", "change"]):
            return 7, "Basic validation: Response contains stock-related keywords"
        
        if test_type == "fundamentals" and any(word in response.lower() for word in ["pe", "ratio", "market cap"]):
            return 7, "Basic validation: Response contains fundamentals keywords"
        
        return 5, "Basic validation: Response appears relevant but unclear quality"
    
    def extract_rating(self, validation_content: str) -> int:
        """Extract numerical rating from AI validation response"""
        try:
            # Look for rating patterns
            import re
            
            # Pattern 1: "Rate (1-10): 9" or "Rating: 9"
            rating_match = re.search(r'rate.*?(\d+)', validation_content.lower())
            if rating_match:
                return int(rating_match.group(1))
            
            # Pattern 2: "9/10" or "9 out of 10"
            rating_match = re.search(r'(\d+)/10', validation_content.lower())
            if rating_match:
                return int(rating_match.group(1))
            
            # Pattern 3: Just a number that could be a rating
            numbers = re.findall(r'\b(\d+)\b', validation_content)
            for num in numbers:
                num_int = int(num)
                if 1 <= num_int <= 10:
                    return num_int
            
            # Default if no rating found
            return 5
            
        except Exception as e:
            print(f"   ⚠️  Rating extraction failed: {e}")
            return 5
    
    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case and validate the response"""
        print(f"\n🧪 Running Test: {test_case['id']}")
        print(f"   📋 Description: {test_case['description']}")
        print(f"   ❓ Question: {test_case['question']}")
        print(f"   🎯 Expected Tool: {test_case['expected_tool']}")
        
        # Get AI response
        start_time = time.time()
        response = self.get_ai_response(test_case['question'])
        response_time = time.time() - start_time
        
        # Determine test type for validation
        test_type = test_case['expected_tool'].replace('get_', '').replace('_', ' ')
        
        # Validate response with AI
        rating, validation_details = self.validate_response_with_ai(
            test_case['question'], response, test_type
        )
        
        # Check if response meets threshold
        meets_threshold = rating >= 9
        
        # Prepare test result
        result = {
            "test_id": test_case['id'],
            "question": test_case['question'],
            "expected_tool": test_case['expected_tool'],
            "response": response,
            "response_time": round(response_time, 2),
            "ai_rating": rating,
            "validation_details": validation_details,
            "meets_threshold": meets_threshold,
            "status": "✅ PASS" if meets_threshold else "❌ FAIL"
        }
        
        print(f"   ⏱️  Response Time: {response_time:.2f}s")
        print(f"   🎯 AI Rating: {rating}/10")
        print(f"   📊 Meets Threshold (9+): {'✅ YES' if meets_threshold else '❌ NO'}")
        print(f"   📝 Status: {result['status']}")
        
        return result
    
    def run_all_tests(self) -> List[Dict]:
        """Run all test cases"""
        print("🚀 Finance Copilot - AI-Driven Test Suite")
        print("=" * 60)
        print("🎯 Threshold for good response: 9/10")
        print("🔍 Using AI validation strategy")
        print("=" * 60)
        
        results = []
        
        for test_case in self.test_cases:
            try:
                result = self.run_test_case(test_case)
                results.append(result)
                
                # Add delay between tests to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Test failed with exception: {e}")
                error_result = {
                    "test_id": test_case['id'],
                    "question": test_case['question'],
                    "expected_tool": test_case['expected_tool'],
                    "response": f"Test failed: {str(e)}",
                    "response_time": 0,
                    "ai_rating": 1,
                    "validation_details": f"Test execution failed: {str(e)}",
                    "meets_threshold": False,
                    "status": "❌ ERROR"
                }
                results.append(error_result)
        
        return results
    
    def generate_report(self, results: List[Dict]) -> str:
        """Generate comprehensive test report"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['meets_threshold'])
        failed_tests = total_tests - passed_tests
        
        # Calculate average rating
        ratings = [r['ai_rating'] for r in results if r['ai_rating'] > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Calculate average response time
        response_times = [r['response_time'] for r in results if r['response_time'] > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        report = f"""
📊 AI-DRIVEN TEST REPORT
{'='*60}

🎯 TEST SUMMARY:
   Total Tests: {total_tests}
   ✅ Passed (9+ rating): {passed_tests}
   ❌ Failed (<9 rating): {failed_tests}
   📊 Success Rate: {(passed_tests/total_tests*100):.1f}%

📈 PERFORMANCE METRICS:
   🎯 Average AI Rating: {avg_rating:.1f}/10
   ⏱️  Average Response Time: {avg_response_time:.2f}s

🔍 DETAILED RESULTS:
"""
        
        for result in results:
            report += f"""
🧪 {result['test_id']}: {result['status']}
   ❓ Question: {result['question']}
   🎯 Expected Tool: {result['expected_tool']}
   ⏱️  Response Time: {result['response_time']}s
   🎯 AI Rating: {result['ai_rating']}/10
   📝 Response Preview: {result['response'][:100]}...
"""
        
        # Add recommendations
        if failed_tests > 0:
            report += f"""
⚠️  RECOMMENDATIONS:
   - {failed_tests} tests failed to meet the 9/10 threshold
   - Review failed responses for common patterns
   - Check if tools are properly integrated
   - Verify API keys and external service availability
"""
        else:
            report += f"""
🎉 EXCELLENT RESULTS:
   - All tests passed the 9/10 threshold!
   - AI tools are working correctly
   - Response quality meets expectations
"""
        
        return report
    
    def save_results(self, results: List[Dict], filename: str = "ai_test_results.json"):
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
        tester = AIDrivenTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_report(results)
        print(report)
        
        # Save results
        tester.save_results(results)
        
        # Summary
        passed = sum(1 for r in results if r['meets_threshold'])
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


