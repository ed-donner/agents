# models/company.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class Sector(str, Enum):
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    ENERGY = "energy"
    HEALTHCARE = "healthcare"
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    MATERIALS = "materials"
    UTILITIES = "utilities"

class Market(str, Enum):
    GLOBAL = "global"
    USA = "usa"
    EUROPE = "europe"
    TURKEY = "turkey"
    ASIA = "asia"

class CompanyFinancials(BaseModel):
    revenue: float
    profit_margin: float
    debt_to_equity: float
    roe: float
    pe_ratio: float
    market_cap: float
    quarterly_growth: float

class GeopoliticalFactor(BaseModel):
    factor_type: str
    impact_level: str  # high, medium, low
    description: str
    affected_sectors: List[Sector]
    timeframe: str

class CompanyProfile(BaseModel):
    name: str
    ticker: str
    sector: Sector
    market: Market
    description: str
    financials: CompanyFinancials
    growth_strategy: str
    competitive_advantages: List[str]
    risks: List[str]
    geopolitical_exposure: List[GeopoliticalFactor]

# models/investment_strategy.py
class TimeHorizon(str, Enum):
    ONE_MONTH = "1_month"
    THREE_MONTHS = "3_months"
    SIX_MONTHS = "6_months"
    ONE_YEAR = "1_year"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class InvestmentRecommendation(BaseModel):
    company: CompanyProfile
    recommendation: str  # BUY, HOLD, SELL
    confidence_score: float = Field(ge=0, le=100)
    target_price: float
    stop_loss: float
    time_horizon: TimeHorizon
    risk_level: RiskLevel
    expected_return: float
    reasoning: str
    key_catalysts: List[str]
    risk_factors: List[str]

class PortfolioStrategy(BaseModel):
    recommendations: List[InvestmentRecommendation]
    diversification_score: float
    overall_risk: RiskLevel
    expected_portfolio_return: float
    rebalancing_suggestions: List[str]
    market_outlook: str
    geopolitical_considerations: str
