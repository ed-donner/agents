"""Serious-tone sales email generator."""

from .models import get_model
from .sales_agent_maker import make_sales_agent

serious_sales_agent = make_sales_agent("Serious Sales Agent", "serious", get_model("gemini"))
