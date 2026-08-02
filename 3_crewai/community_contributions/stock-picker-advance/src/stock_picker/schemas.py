from pydantic import BaseModel, Field, RootModel
from typing import List, Optional


class CompanyBrief(BaseModel):
    ticker: str = Field(..., description="Exchange ticker, e.g., AAPL")
    name: str
    exchange: Optional[str] = None
    country: Optional[str] = None
    industry_match_reason: Optional[str] = None


class ScreenerMetrics(BaseModel):
    ticker: str
    name: str
    market_cap: Optional[float] = None
    pe_ttm: Optional[float] = None
    ev_ebitda: Optional[float] = None
    revenue_cagr_3y: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    fcf_margin_ttm: Optional[float] = None
    net_debt_to_ebitda: Optional[float] = None
    dividend_yield: Optional[float] = None
    notes: Optional[str] = None


class ValuationView(BaseModel):
    ticker: str
    name: str
    intrinsic_estimate_note: Optional[str] = None
    rel_valuation_score: Optional[float] = None  # higher is better
    quality_score: Optional[float] = None
    growth_score: Optional[float] = None


class RiskNewsItem(BaseModel):
    ticker: str
    headline: str
    url: Optional[str] = None
    sentiment: Optional[str] = None
    risk_note: Optional[str] = None


class FinalPick(BaseModel):
    ticker: str
    name: str
    thesis: str
    key_drivers: List[str]
    red_flags: List[str]
    est_one_year_view: Optional[str] = None


class FinalShortlist(BaseModel):
    picks: List[FinalPick]


# Root models to enable list outputs for CrewAI Task.output_json
class CompanyBriefList(RootModel[List[CompanyBrief]]):
    pass


class ScreenerMetricsList(RootModel[List[ScreenerMetrics]]):
    pass


class ValuationViewList(RootModel[List[ValuationView]]):
    pass


class RiskNewsItemList(RootModel[List[RiskNewsItem]]):
    pass
