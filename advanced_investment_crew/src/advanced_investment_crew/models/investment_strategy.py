from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from .company import CompanyProfile


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




