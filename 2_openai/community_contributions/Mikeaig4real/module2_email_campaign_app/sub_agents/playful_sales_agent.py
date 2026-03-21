"""Playful-tone sales email generator."""

from .models import get_model
from .sales_agent_maker import make_sales_agent

playful_sales_agent = make_sales_agent("Playful Sales Agent", "playful", get_model("anthropic"))