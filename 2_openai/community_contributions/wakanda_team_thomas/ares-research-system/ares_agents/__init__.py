"""ARES agents package — agent definitions."""

from .architect import architect_agent
from .web_specialist import web_specialist_agent
from .report_editor import report_editor_agent
from .notificator import notification_agent

__all__ = [
    "architect_agent",
    "web_specialist_agent",
    "report_editor_agent",
    "notification_agent",
]
