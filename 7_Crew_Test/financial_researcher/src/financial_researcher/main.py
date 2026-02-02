#!/usr/bin/env python
# src/financial_researcher/main.py
import os
from financial_researcher.crew import FinancialAnalysisCrew

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the comprehensive financial analysis crew.
    """
    inputs = {
        'company': 'Apple Inc.',
        'symbol': 'AAPL'
    }

    print(f"🚀 Starting comprehensive financial analysis for {inputs['company']} ({inputs['symbol']})")
    print("=" * 80)
    
    # Create and run the crew
    result = FinancialAnalysisCrew().crew().kickoff(inputs=inputs)

    print("\n\n" + "=" * 80)
    print("📊 COMPREHENSIVE INVESTMENT ANALYSIS COMPLETE")
    print("=" * 80)
    print(result.raw)

    print(f"\n📄 Detailed investment report saved to: output/investment_report.md")
    print("⚠️  DISCLAIMER: This analysis is for informational purposes only.")

if __name__ == "__main__":
    run()
