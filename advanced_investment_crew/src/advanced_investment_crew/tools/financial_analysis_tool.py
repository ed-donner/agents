from typing import List, Type

import yfinance as yf
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class FinancialAnalysisInput(BaseModel):
    ticker: str = Field(..., description="Company ticker")
    analysis_depth: str = Field(default="comprehensive", description="Analysis depth")


class FinancialAnalysisTool(BaseTool):
    name: str = "Financial Statement Analyzer"
    description: str = """
    Deep financial analysis including:
    - Income statement analysis
    - Balance sheet health
    - Cash flow analysis
    - Profitability ratios
    - Liquidity ratios
    - Solvency ratios
    - Growth metrics
    - Peer comparison
    """
    args_schema: Type[BaseModel] = FinancialAnalysisInput

    def _run(self, ticker: str, analysis_depth: str = "comprehensive") -> dict:
        stock = yf.Ticker(ticker)

        income_stmt = getattr(stock, "financials", None)
        balance_sheet = getattr(stock, "balance_sheet", None)
        cash_flow = getattr(stock, "cashflow", None)

        analysis = {
            "profitability": self._analyze_profitability(income_stmt),
            "liquidity": self._analyze_liquidity(balance_sheet),
            "solvency": self._analyze_solvency(balance_sheet),
            "efficiency": self._analyze_efficiency(income_stmt, balance_sheet),
            "growth": self._analyze_growth(income_stmt, cash_flow),
            "valuation": self._analyze_valuation(stock),
            "peer_comparison": self._compare_peers(ticker),
            "red_flags": [],
            "strengths": [],
        }

        return analysis

    # Placeholder helper methods
    def _analyze_profitability(self, income_stmt):
        return {"metrics": "pending_data", "source_available": income_stmt is not None}

    def _analyze_liquidity(self, balance_sheet):
        return {"metrics": "pending_data", "source_available": balance_sheet is not None}

    def _analyze_solvency(self, balance_sheet):
        return {"metrics": "pending_data", "source_available": balance_sheet is not None}

    def _analyze_efficiency(self, income_stmt, balance_sheet):
        return {"metrics": "pending_data"}

    def _analyze_growth(self, income_stmt, cash_flow):
        return {"metrics": "pending_data"}

    def _analyze_valuation(self, stock):
        info = getattr(stock, "info", {}) or {}
        return {
            "market_cap": info.get("marketCap", None),
            "pe_ratio": info.get("trailingPE", None),
            "pb_ratio": info.get("priceToBook", None),
        }

    def _compare_peers(self, ticker: str):
        return {"peers": [], "note": f"Peer comparison for {ticker} pending integration"}




