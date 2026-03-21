"""Engaging-tone sales email generator."""

from .models import get_model
from .sales_agent_maker import make_sales_agent

engaging_sales_agent = make_sales_agent("Engaging Sales Agent", "engaging", get_model("gemini"))
