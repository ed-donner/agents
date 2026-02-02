# tools/market_data_tool.py
from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class MarketDataInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    period: str = Field(default="10y", description="Historical period (1mo, 3mo, 6mo, 1y, 5y, 10y)")
    market: str = Field(default="global", description="Market region")

class MarketDataTool(BaseTool):
    name: str = "Market Data Analyzer"
    description: str = """
    Fetches comprehensive market data including:
    - 10-year historical price data
    - Volume analysis
    - Technical indicators (MA, RSI, MACD)
    - Market correlations
    - Sector performance
    """
    args_schema: Type[BaseModel] = MarketDataInput

    def _run(self, ticker: str, period: str = "10y", market: str = "global") -> dict:
        try:
            # Fetch data from multiple sources
            stock = yf.Ticker(ticker)
            
            # Historical data
            hist = stock.history(period=period)
            
            # Calculate technical indicators
            hist['MA_50'] = hist['Close'].rolling(window=50).mean()
            hist['MA_200'] = hist['Close'].rolling(window=200).mean()
            hist['RSI'] = self._calculate_rsi(hist['Close'])
            
            # Get fundamental data
            info = stock.info
            
            return {
                "ticker": ticker,
                "current_price": hist['Close'].iloc[-1],
                "52_week_high": hist['High'].max(),
                "52_week_low": hist['Low'].min(),
                "average_volume": hist['Volume'].mean(),
                "market_cap": info.get('marketCap', 0),
                "pe_ratio": info.get('trailingPE', 0),
                "dividend_yield": info.get('dividendYield', 0),
                "beta": info.get('beta', 1.0),
                "technical_indicators": {
                    "ma_50": hist['MA_50'].iloc[-1],
                    "ma_200": hist['MA_200'].iloc[-1],
                    "rsi": hist['RSI'].iloc[-1]
                },
                "historical_data": hist.tail(30).to_dict()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


# tools/geopolitical_analysis_tool.py
class GeopoliticalAnalysisInput(BaseModel):
    region: str = Field(..., description="Geographic region or country")
    sectors: List[str] = Field(..., description="Sectors to analyze")
    timeframe: str = Field(default="current", description="Analysis timeframe")

class GeopoliticalAnalysisTool(BaseTool):
    name: str = "Geopolitical Risk Analyzer"
    description: str = """
    Analyzes geopolitical factors affecting investments:
    - Political stability indices
    - Trade relations and tariffs
    - Regulatory changes
    - International conflicts
    - Economic sanctions
    - Currency risks
    - Turkey-specific political and economic factors
    """
    args_schema: Type[BaseModel] = GeopoliticalAnalysisInput

    def _run(self, region: str, sectors: List[str], timeframe: str = "current") -> dict:
        # Integration with news APIs, geopolitical databases
        # GDELT, World Bank, IMF, CBRT (for Turkey)
        
        analysis = {
            "region": region,
            "political_stability_score": self._get_stability_score(region),
            "trade_relations": self._analyze_trade_relations(region),
            "regulatory_environment": self._assess_regulations(region, sectors),
            "currency_risk": self._evaluate_currency_risk(region),
            "sector_impacts": self._analyze_sector_impacts(region, sectors),
            "key_risks": [],
            "opportunities": [],
            "recommendations": []
        }
        
        if region.lower() == "turkey":
            analysis["turkey_specific"] = {
                "central_bank_policy": "Current monetary policy stance",
                "inflation_outlook": "Inflation trends and forecasts",
                "foreign_relations": "Key bilateral relationships",
                "eu_relations": "EU accession process impact",
                "regional_conflicts": "Syria, Libya, Eastern Mediterranean"
            }
        
        return analysis


# tools/financial_analysis_tool.py
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
        
        # Get financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow
        
        analysis = {
            "profitability": self._analyze_profitability(income_stmt),
            "liquidity": self._analyze_liquidity(balance_sheet),
            "solvency": self._analyze_solvency(balance_sheet),
            "efficiency": self._analyze_efficiency(income_stmt, balance_sheet),
            "growth": self._analyze_growth(income_stmt, cash_flow),
            "valuation": self._analyze_valuation(stock),
            "peer_comparison": self._compare_peers(ticker),
            "red_flags": [],
            "strengths": []
        }
        
        return analysis


# tools/sentiment_analysis_tool.py
class SentimentAnalysisInput(BaseModel):
    company_name: str = Field(..., description="Company name")
    ticker: str = Field(..., description="Stock ticker")
    lookback_days: int = Field(default=30, description="Days to look back")

class SentimentAnalysisTool(BaseTool):
    name: str = "Market Sentiment Analyzer"
    description: str = """
    Analyzes market sentiment from multiple sources:
    - News sentiment (global and Turkish media)
    - Social media sentiment (Twitter, Reddit, Ekşi Sözlük)
    - Analyst ratings and price targets
    - Insider trading activity
    - Institutional ownership changes
    """
    args_schema: Type[BaseModel] = SentimentAnalysisInput

    def _run(self, company_name: str, ticker: str, lookback_days: int = 30) -> dict:
        # Integration with NewsAPI, Twitter API, Reddit API
        # Turkish sources: Hürriyet, Sözcü, Bloomberg HT, etc.
        
        sentiment = {
            "overall_sentiment": "positive/negative/neutral",
            "sentiment_score": 0.0,  # -1 to 1
            "news_sentiment": self._analyze_news_sentiment(company_name, lookback_days),
            "social_sentiment": self._analyze_social_sentiment(ticker, lookback_days),
            "analyst_consensus": self._get_analyst_consensus(ticker),
            "insider_activity": self._analyze_insider_trading(ticker),
            "institutional_flow": self._analyze_institutional_activity(ticker),
            "trending_topics": [],
            "sentiment_trend": "improving/declining/stable"
        }
        
        return sentiment


# tools/risk_assessment_tool.py
class RiskAssessmentInput(BaseModel):
    ticker: str = Field(..., description="Stock ticker")
    time_horizon: str = Field(..., description="Investment time horizon")
    portfolio_context: dict = Field(default={}, description="Existing portfolio")

class RiskAssessmentTool(BaseTool):
    name: str = "Comprehensive Risk Assessor"
    description: str = """
    Evaluates multiple risk dimensions:
    - Market risk (beta, volatility)
    - Credit risk
    - Liquidity risk
    - Operational risk
    - Geopolitical risk
    - Currency risk
    - Sector-specific risks
    - Company-specific risks
    - Portfolio diversification risk
    """
    args_schema: Type[BaseModel] = RiskAssessmentInput

    def _run(self, ticker: str, time_horizon: str, portfolio_context: dict = {}) -> dict:
        risk_assessment = {
            "overall_risk_score": 0.0,  # 0-100
            "risk_level": "low/medium/high/very_high",
            "market_risk": self._assess_market_risk(ticker),
            "credit_risk": self._assess_credit_risk(ticker),
            "liquidity_risk": self._assess_liquidity_risk(ticker),
            "geopolitical_risk": self._assess_geopolitical_risk(ticker),
            "currency_risk": self._assess_currency_risk(ticker),
            "var_95": 0.0,  # Value at Risk
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "risk_factors": [],
            "mitigation_strategies": [],
            "diversification_benefit": self._calculate_diversification(ticker, portfolio_context)
        }
        
        return risk_assessment
