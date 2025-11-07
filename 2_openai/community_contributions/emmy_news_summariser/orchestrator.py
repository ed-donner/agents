"""Orchestrator for coordinating news summary workflow."""

from typing import Tuple
from agents import (
    news_aggregator_agent,
    summarizer_agent,
    audio_generator_agent,
    aggregate_news,
    summarize_articles_async,
    synthesize_speech,
)


class NewsSummaryOrchestrator:
    """Orchestrates the news summary workflow using multiple agents."""
    
    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.aggregator = news_aggregator_agent
        self.summarizer = summarizer_agent
        self.audio_generator = audio_generator_agent
    
    async def orchestrate(self, topic: str) -> Tuple[str, str]:
        """Orchestrate the complete news summary workflow.
        
        Args:
            topic: News topic to summarize
            
        Returns:
            Tuple of (summary_text, audio_file_path)
        """
        # Step 1: Aggregate news using the aggregator agent's tool
        articles_result = await aggregate_news(topic)
        articles = articles_result["articles"]
        
        # Step 2: Summarize using the summarizer agent's tool
        summary = await summarize_articles_async(articles)
        
        # Step 3: Generate audio using the audio generator agent's tool
        audio_path = await synthesize_speech(summary)
        
        return summary, audio_path
