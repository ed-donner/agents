#!/usr/bin/env python
import os
import warnings
from datetime import datetime

from financial_advisory.crew import FinancialAdvisory

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs("output", exist_ok=True)


def run():
    """
    Run the crew.
    """
    # User inputs on total family members, earninig members, total monthly earnings, monthly expenses, savings,
    # debts, investment preferences, insurance details, financial goals and number of children, age of oldest member
    # and age of youngest member
    user_info = (
        f"total_family_members: 3\n"
        f"earning_members: 2\n"
        f"country: India\n"
        f"local_currency: INR\n"
        f"monthly_earnings: 100000\n"
        f"monthly_expenses: 50000\n"
        f"savings: 50000\n"
        f"debts: 100000\n"
        f"investment_preferences: moderate risk\n"
        f"insurance_details: health_insurance=True, life_insurance=False, property_insurance=False\n"
        f"financial_goals: buy a house (1cr, 5 years); children's education (2000000, 14 years); retirement (4cr, 25 years)\n"
        f"number_of_children: 2\n"
        f"age_of_oldest_member: 34\n"
        f"age_of_youngest_member: 4\n"
        f"report_date: {datetime.now().strftime('%Y-%m-%d')}\n"
    )

    inputs = {"user_info": user_info}

    try:
        result = FinancialAdvisory().financial_advisory_crew().kickoff(inputs=inputs)

        # print result
        print("\n\n=== FINAL REPORT ===\n\n")
        print(result.raw)
        print("\n\nReport has been saved to output/financial_plan_report.md")
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


if __name__ == "__main__":
    run()
