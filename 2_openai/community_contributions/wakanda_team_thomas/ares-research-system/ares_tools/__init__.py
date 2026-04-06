"""ARES tools package — function tools for agent use."""

from .search import tavily_web_search
from .email import send_email

__all__ = [
    "tavily_web_search",
    "send_email",
]
