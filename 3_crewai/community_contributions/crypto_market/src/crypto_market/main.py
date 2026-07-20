import sys
import warnings
import os

from crypto_market.crew import CryptoMarket

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run():
    """
    Run the crypto research crew.
    """
    # Create memory directory if it doesn't exist
    os.makedirs('memory', exist_ok=True)
    
    inputs = {
        'market_focus': 'DeFi protocols',
    }

    # Create and run the crew
    result = CryptoMarket().crew().kickoff(inputs=inputs)

    # Print the result
    print("\n\n=== FINAL DECISION ===\n\n")
    print(result.raw)


if __name__ == "__main__":
    run()
