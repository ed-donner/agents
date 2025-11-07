"""Agents module for news summarizer application."""

from .base import Agent, function_tool
from .news_aggregator import news_aggregator_agent, aggregate_news
from .summarizer import summarizer_agent, summarize_articles_async
from .audio_generator import audio_generator_agent, synthesize_speech

__all__ = [
    "Agent",
    "function_tool",
    "news_aggregator_agent",
    "summarizer_agent",
    "audio_generator_agent",
    "aggregate_news",
    "summarize_articles_async",
    "synthesize_speech",
]
