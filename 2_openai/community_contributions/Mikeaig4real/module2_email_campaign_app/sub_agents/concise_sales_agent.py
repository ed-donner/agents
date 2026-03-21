"""Concise-tone sales email generator."""

from .models import get_model
from .sales_agent_maker import make_sales_agent

concise_sales_agent = make_sales_agent("Concise Sales Agent", "concise", get_model("deepseek"))
