"""ARES tools package — function tools for agent use."""

from .search import travily_web_search
from .email import send_email

__all__ = [
    "travily_web_search",
    "send_email",
]
