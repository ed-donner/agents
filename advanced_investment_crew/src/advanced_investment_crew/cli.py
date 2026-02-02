"""
CLI entry to fetch data and run basic optimization without UI.

Usage:
  python -m advanced_investment_crew.cli --market global --tickers SPY QQQ VTI
"""

import argparse
import json

import pandas as pd

from advanced_investment_crew.analysis.portfolio_optimizer import PortfolioOptimizer
from advanced_investment_crew.data.market_data import MarketDataFetcher


def run_cli():
    parser = argparse.ArgumentParser(description="Advanced Investment CLI")
    parser.add_argument("--market", default="global", choices=["global", "turkey"])
    parser.add_argument("--tickers", nargs="*", help="Override ticker list")
    parser.add_argument("--target_vol", type=float, default=None)
    parser.add_argument("--lambda_reg", type=float, default=0.0)
    parser.add_argument("--long_only", action="store_true", default=False)
    parser.add_argument("--min_w", type=float, default=None, help="Min weight bound")
    parser.add_argument("--max_w", type=float, default=None, help="Max weight bound")
    parser.add_argument("--max_gross", type=float, default=None, help="Max gross leverage (L1 cap)")
    parser.add_argument(
        "--sector_cap",
        action="append",
        help="Sector cap as sector=0.4 (can be passed multiple times)",
    )
    args = parser.parse_args()

    fetcher = MarketDataFetcher(market_type=args.market)
    tickers = args.tickers or fetcher.get_default_tickers()

    print(f"Market: {args.market}")
    print(f"Tickers: {', '.join(tickers)}")

    data = fetcher.fetch_data(tickers=tickers)
    prices = data["Close"] if "Close" in data else data
    returns = prices.pct_change().dropna()

    opt = PortfolioOptimizer(market_type=args.market)
    weight_bounds = None
    if args.min_w is not None or args.max_w is not None:
        weight_bounds = (
            args.min_w if args.min_w is not None else -1.0,
            args.max_w if args.max_w is not None else 1.0,
        )

    sector_caps = None
    sector_map = None
    if args.sector_cap:
        sector_caps = {}
        for item in args.sector_cap:
            if "=" in item:
                k, v = item.split("=", 1)
                try:
                    sector_caps[k] = float(v)
                except ValueError:
                    pass
        # build sector map from metadata when caps are provided
        sector_map = fetcher.get_sector_map() or {t: "generic" for t in tickers}
    else:
        # If no caps passed, still expose sector map (for future use)
        sector_map = fetcher.get_sector_map()

    weights = opt.optimize_portfolio(
        returns,
        target_vol=args.target_vol,
        lambda_reg=args.lambda_reg,
        long_only=args.long_only,
        weight_bounds=weight_bounds,
        max_gross_leverage=args.max_gross,
        sector_map=sector_map,
        sector_caps=sector_caps,
    )

    print("\nSuggested weights:")
    print(json.dumps(weights, indent=2))


if __name__ == "__main__":
    run_cli()


