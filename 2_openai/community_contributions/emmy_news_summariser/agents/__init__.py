"""News agents module for news summarizer application."""

# Our custom agent instances (they import from openai-agents SDK internally)
from .news_aggregator import news_aggregator_agent, aggregate_news
from .summarizer import summarizer_agent
from .audio_generator import audio_generator_agent, synthesize_speech

__all__ = [
    "news_aggregator_agent",
    "summarizer_agent",
    "audio_generator_agent",
    "aggregate_news",
    "synthesize_speech",
]
