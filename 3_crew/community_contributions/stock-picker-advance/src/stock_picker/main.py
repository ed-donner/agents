import argparse
from dotenv import load_dotenv

from .crew import StockPickerCrew


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--industry", required=True)
    p.add_argument("--region", default="global")
    p.add_argument("--n-picks", type=int, default=5)
    p.add_argument("--min-mcap", type=int, default=500_000_000)
    p.add_argument(
        "--valuation-pref", default="balanced", choices=["value", "growth", "balanced"]
    )
    return p.parse_args()


if __name__ == "__main__":
    load_dotenv()  # load OPENAI_API_KEY, SERPER_API_KEY, etc. from .env if present

    args = parse_args()

    crew = StockPickerCrew().crew()

    # These will be available in agents/tasks YAML as {industry}, {region}, etc.
    inputs = {
        "industry": args.industry,
        "region": args.region,
        "n_picks": args.n_picks,
        "min_mcap": args.min_mcap,
        "valuation_pref": args.valuation_pref,
    }

    result = crew.kickoff(inputs=inputs)
    print("\n=== FINAL SHORTLIST (raw) ===\n")
    print(result)

