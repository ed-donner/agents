# src/financial_researcher/tools/financial_tools.py
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

try:
    import yfinance as yf
    import pandas as pd
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not installed. Install with: pip install yfinance pandas")

class StockDataToolInput(BaseModel):
    """Input schema for StockDataTool."""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    period: str = Field(default="1y", description="Period for data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")

class StockDataTool(BaseTool):
    name: str = "Stock Data Fetcher"
    description: str = (
        "Fetches comprehensive stock data including price history, volume, "
        "financial ratios, and company information for investment analysis."
    )
    args_schema: Type[BaseModel] = StockDataToolInput

    def _run(self, symbol: str, period: str = "1y") -> str:
        if not YFINANCE_AVAILABLE:
            return "Error: yfinance package not installed. Please install with: pip install yfinance pandas"
        
        try:
            stock = yf.Ticker(symbol)
            
            # Get stock info
            info = stock.info
            
            # Get historical data
            hist = stock.history(period=period)
            
            if hist.empty:
                return f"No historical data found for {symbol}"
            
            # Calculate some basic metrics
            current_price = info.get('currentPrice', hist['Close'].iloc[-1])
            price_change = hist['Close'].iloc[-1] - hist['Close'].iloc[0]
            price_change_pct = (price_change / hist['Close'].iloc[0]) * 100
            
            # Format market cap
            market_cap = info.get('marketCap')
            market_cap_str = f"${market_cap:,}" if market_cap else 'N/A'
            
            # Format employees
            employees = info.get('fullTimeEmployees')
            employees_str = f"{employees:,}" if employees else 'N/A'
            
            # Format revenue
            revenue = info.get('totalRevenue')
            revenue_str = f"${revenue:,}" if revenue else 'N/A'
            
            # Format margins and ratios
            profit_margin = info.get('profitMargins')
            profit_margin_str = f"{profit_margin:.2%}" if profit_margin else 'N/A'
            
            roe = info.get('returnOnEquity')
            roe_str = f"{roe:.2%}" if roe else 'N/A'
            
            roa = info.get('returnOnAssets')
            roa_str = f"{roa:.2%}" if roa else 'N/A'
            
            dividend_yield = info.get('dividendYield')
            dividend_yield_str = f"{dividend_yield:.2%}" if dividend_yield else 'N/A'
            
            payout_ratio = info.get('payoutRatio')
            payout_ratio_str = f"{payout_ratio:.2%}" if payout_ratio else 'N/A'
            
            # Format volume
            volume = info.get('volume')
            volume_str = f"{volume:,}" if volume else 'N/A'
            
            avg_volume = info.get('averageVolume')
            avg_volume_str = f"{avg_volume:,}" if avg_volume else 'N/A'
            
            shares_outstanding = info.get('sharesOutstanding')
            shares_str = f"{shares_outstanding:,}" if shares_outstanding else 'N/A'
            
            float_shares = info.get('floatShares')
            float_str = f"{float_shares:,}" if float_shares else 'N/A'

            result = f"""
Stock Analysis for {symbol}:

Company Information:
- Name: {info.get('longName', 'N/A')}
- Sector: {info.get('sector', 'N/A')}
- Industry: {info.get('industry', 'N/A')}
- Market Cap: {market_cap_str}
- Employees: {employees_str}

Valuation Metrics:
- Current Price: ${current_price:.2f}
- P/E Ratio: {info.get('trailingPE', 'N/A')}
- Forward P/E: {info.get('forwardPE', 'N/A')}
- P/B Ratio: {info.get('priceToBook', 'N/A')}
- P/S Ratio: {info.get('priceToSalesTrailing12Months', 'N/A')}
- PEG Ratio: {info.get('pegRatio', 'N/A')}

Performance Metrics:
- 52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
- 52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}
- Price Change ({period}): ${price_change:.2f} ({price_change_pct:+.2f}%)
- Beta: {info.get('beta', 'N/A')}

Financial Health:
- Revenue (TTM): {revenue_str}
- Profit Margin: {profit_margin_str}
- ROE: {roe_str}
- ROA: {roa_str}
- Debt to Equity: {info.get('debtToEquity', 'N/A')}

Dividend Information:
- Dividend Yield: {dividend_yield_str}
- Dividend Rate: ${info.get('dividendRate', 'N/A')}
- Payout Ratio: {payout_ratio_str}

Trading Information:
- Volume: {volume_str}
- Average Volume: {avg_volume_str}
- Shares Outstanding: {shares_str}
- Float: {float_str}

Historical Data Summary:
- Period Analyzed: {period}
- Data Points: {len(hist)}
- Price Range: ${hist['Close'].min():.2f} - ${hist['Close'].max():.2f}
- Average Daily Volume: {hist['Volume'].mean():,.0f}
"""
            
            return result
            
        except Exception as e:
            return f"Error fetching stock data for {symbol}: {str(e)}"

class FinancialRatiosToolInput(BaseModel):
    """Input schema for FinancialRatiosTool."""
    symbol: str = Field(..., description="Stock symbol for ratio analysis")

class FinancialRatiosTool(BaseTool):
    name: str = "Financial Ratios Calculator"
    description: str = (
        "Calculates and analyzes comprehensive financial ratios for "
        "investment decision making and company valuation."
    )
    args_schema: Type[BaseModel] = FinancialRatiosToolInput

    def _run(self, symbol: str) -> str:
        if not YFINANCE_AVAILABLE:
            return "Error: yfinance package not installed. Please install with: pip install yfinance pandas"
        
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Profitability Ratios
            profitability = {
                'Gross Margin': info.get('grossMargins'),
                'Operating Margin': info.get('operatingMargins'),
                'Net Profit Margin': info.get('profitMargins'),
                'Return on Equity (ROE)': info.get('returnOnEquity'),
                'Return on Assets (ROA)': info.get('returnOnAssets'),
                'Return on Investment (ROI)': info.get('returnOnInvestment')
            }
            
            # Valuation Ratios
            valuation = {
                'P/E Ratio (Trailing)': info.get('trailingPE'),
                'P/E Ratio (Forward)': info.get('forwardPE'),
                'P/B Ratio': info.get('priceToBook'),
                'P/S Ratio': info.get('priceToSalesTrailing12Months'),
                'PEG Ratio': info.get('pegRatio'),
                'EV/Revenue': info.get('enterpriseToRevenue'),
                'EV/EBITDA': info.get('enterpriseToEbitda')
            }
            
            # Liquidity Ratios
            liquidity = {
                'Current Ratio': info.get('currentRatio'),
                'Quick Ratio': info.get('quickRatio'),
                'Cash Ratio': info.get('cashRatio')
            }
            
            # Leverage Ratios
            leverage = {
                'Debt to Equity': info.get('debtToEquity'),
                'Debt to Assets': info.get('totalDebtToTotalAssets'),
                'Interest Coverage': info.get('interestCoverage')
            }
            
            # Efficiency Ratios
            efficiency = {
                'Asset Turnover': info.get('assetTurnover'),
                'Inventory Turnover': info.get('inventoryTurnover'),
                'Receivables Turnover': info.get('receivablesTurnover')
            }
            
            result = f"Comprehensive Financial Ratios Analysis for {symbol}:\n\n"
            
            # Format each category
            categories = [
                ("PROFITABILITY RATIOS", profitability),
                ("VALUATION RATIOS", valuation),
                ("LIQUIDITY RATIOS", liquidity),
                ("LEVERAGE RATIOS", leverage),
                ("EFFICIENCY RATIOS", efficiency)
            ]
            
            for category_name, ratios in categories:
                result += f"{category_name}:\n"
                result += "-" * len(category_name) + "\n"
                
                for ratio_name, value in ratios.items():
                    if value is not None:
                        if ratio_name in ['Gross Margin', 'Operating Margin', 'Net Profit Margin', 'ROE', 'ROA', 'ROI']:
                            result += f"• {ratio_name}: {value:.2%}\n"
                        else:
                            result += f"• {ratio_name}: {value:.2f}\n"
                    else:
                        result += f"• {ratio_name}: N/A\n"
                
                result += "\n"
            
            # Add interpretation
            result += "RATIO INTERPRETATION:\n"
            result += "=" * 20 + "\n"
            
            pe_ratio = info.get('trailingPE')
            if pe_ratio:
                if pe_ratio < 15:
                    result += "• P/E Ratio: Potentially undervalued (< 15)\n"
                elif pe_ratio > 25:
                    result += "• P/E Ratio: Potentially overvalued (> 25)\n"
                else:
                    result += "• P/E Ratio: Fairly valued (15-25 range)\n"
            
            roe = info.get('returnOnEquity')
            if roe:
                if roe > 0.15:
                    result += "• ROE: Excellent (> 15%)\n"
                elif roe > 0.10:
                    result += "• ROE: Good (10-15%)\n"
                else:
                    result += "• ROE: Below average (< 10%)\n"
            
            debt_to_equity = info.get('debtToEquity')
            if debt_to_equity:
                if debt_to_equity < 0.3:
                    result += "• Debt/Equity: Conservative debt level (< 0.3)\n"
                elif debt_to_equity > 0.6:
                    result += "• Debt/Equity: High debt level (> 0.6)\n"
                else:
                    result += "• Debt/Equity: Moderate debt level (0.3-0.6)\n"
            
            return result
            
        except Exception as e:
            return f"Error calculating financial ratios for {symbol}: {str(e)}"
