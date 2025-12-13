#!/usr/bin/env python
# src/financial_researcher/main.py
import os
from financial_researcher.crew import ResearchCrew
from dotenv import load_dotenv
load_dotenv()
from dotenv import load_dotenv
import os
load_dotenv(override=True)  # ensure .env keys override system vars
print("DEBUG OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the research crew.
    """
    inputs = {
        'company': 'Apple'
    }

    # Create and run the crew
    result = ResearchCrew().crew().kickoff(inputs=inputs)

    # Print the result
    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

    print("\n\nReport has been saved to output/report.md")

if __name__ == "__main__":
    run()