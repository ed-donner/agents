#!/usr/bin/env python
import os
from software_engineering.crew import EngineeringTeam


# Requirements for the project
requirements = """
A trading simulation platform account system.
- Create accounts, deposit, withdraw.
- Record buy/sell shares with quantity.
- Portfolio valuation and P/L calculation.
- Holdings and transaction history.
- Prevent invalid operations.
- Use get_share_price(symbol) with test prices for AAPL, TSLA, GOOGL.

Note: Frontend/UI will be handled separately by the frontend engineer.
"""

def run():
    # Ensure output structure
    os.makedirs('output/backend', exist_ok=True)
    os.makedirs('output/tests', exist_ok=True)

    # Create only the top-level __init__.py
    init_file = os.path.join('output', '__init__.py')
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write('# Package initializer\n')

    inputs = {"requirements": requirements}

    team = EngineeringTeam()
    crew = team.crew()

    print("\n🚀 Starting the EngineeringTeam crew...")
    print("📋 Running design phase (callback will handle dynamic tasks)...\n")

    try:
        # The callback in crew.py will handle the next steps dynamically
        crew.kickoff(inputs=inputs)
        print("\n✅ Design phase complete — dynamic tasks will now execute automatically.\n")

    except Exception as e:
        print(f"\n❌ An error occurred while running the crew: {e}\n")
