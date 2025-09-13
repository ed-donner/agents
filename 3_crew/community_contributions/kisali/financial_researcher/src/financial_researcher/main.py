#!/usr/bin/env python
import os


from financial_researcher.crew import FinancialResearcher

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the crew.
    """
    inputs = {
        'company': 'Safaricom PLC',
    }
    
    try:
        result = FinancialResearcher().crew().kickoff(inputs=inputs)
        print("\n\n=== FINAL REPORT ===\n\n")
        print(result.raw)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

if __name__ == "__main__":
    run()