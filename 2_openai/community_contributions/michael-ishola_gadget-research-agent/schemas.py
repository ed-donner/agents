"""Shared schemas for BudgetBuy AI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProductSpecs(BaseModel):
    spec_1: str = "unknown"
    spec_2: str = "unknown"
    spec_3: str = "unknown"


class Product(BaseModel):
    product_id: str = "unknown-product"
    name: str = "unknown"
    category: str = "unknown"
    brand: str = "unknown"
    price_ngn: int = 0
    warranty_months: int = 0
    availability: str = "unknown"
    battery_life_hours: float = Field(default=0, ge=0)
    key_specs: ProductSpecs = Field(default_factory=ProductSpecs)
    url: str = "unknown"


class ShoppingPlan(BaseModel):
    category: str
    query: str
    hard_constraints: list[str]


class GadgetScopeCheck(BaseModel):
    is_gadget_request: bool
    message: str


class ResearchOutput(BaseModel):
    candidates: list[Product]


class RankedProduct(BaseModel):
    product_id: str
    score: float
    reason: str


class Recommendation(BaseModel):
    best_product_id: str
    shortlist: list[RankedProduct]
    tradeoffs: str
    final_summary: str
    notify_message: str | None = None


class NotificationDispatch(BaseModel):
    status: str

