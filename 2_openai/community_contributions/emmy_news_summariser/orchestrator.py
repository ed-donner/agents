"""Orchestrator for coordinating news summary workflow."""

import json
from typing import Tuple
from agents import (
    news_aggregator_agent,
    summarizer_agent,
    audio_generator_agent,
)


class NewsSummaryOrchestrator:
    """Orchestrates the news summary workflow using multiple autonomous agents.
    
    Each agent decides autonomously when and how to use its tools based on
    the instructions provided to it.
    """
    
    def __init__(self):
        """Initialize the orchestrator with all agents."""
        self.aggregator = news_aggregator_agent
        self.summarizer = summarizer_agent
        self.audio_generator = audio_generator_agent
    
    async def orchestrate(self, topic: str) -> Tuple[str, str]:
        """Orchestrate the complete news summary workflow using autonomous agents.
        
        Each agent autonomously decides how to accomplish its task:
        1. Aggregator agent fetches news articles
        2. Summarizer agent creates a concise summary
        3. Audio generator agent converts to speech
        
        Args:
            topic: News topic to summarize
            
        Returns:
            Tuple of (summary_text, audio_file_path)
        """
        print(f"\n{'='*60}")
        print(f"Starting news summary workflow for topic: {topic}")
        print(f"{'='*60}\n")
        
        # Step 1: Ask the aggregator agent to fetch news
        # The agent will autonomously decide to call aggregate_news
        print("Step 1: Fetching news articles...")
        articles_response = await self.aggregator.run(
            f"Fetch the latest news articles about {topic}",
            return_raw_tool_result=True  # Get raw JSON result from the tool
        )
        
        # Extract articles from the response
        if isinstance(articles_response, dict):
            articles = articles_response.get("articles", [])
        elif isinstance(articles_response, str):
            try:
                articles_data = json.loads(articles_response)
                articles = articles_data.get("articles", [])
            except json.JSONDecodeError:
                raise ValueError(f"Could not parse articles from aggregator response: {articles_response}")
        else:
            raise ValueError(f"Unexpected response type from aggregator: {type(articles_response)}")
        
        print(f"✓ Fetched {len(articles)} articles\n")
        
        # Step 2: Ask the summarizer agent to create a summary
        # The agent will autonomously decide to call summarize_articles
        print("Step 2: Creating summary...")
        summary = await self.summarizer.run(
            f"Summarize these news articles into a 300-word briefing: {json.dumps(articles)}"
        )
        print(f"✓ Summary created ({len(summary.split())} words)\n")
        
        # Step 3: Ask the audio generator agent to create audio
        # The agent will autonomously decide to call synthesize_speech
        print("Step 3: Generating audio...")
        audio_path = await self.audio_generator.run(
            f"Convert this text to speech: {summary}",
            return_raw_tool_result=True  # Get the actual file path from the tool
        )
        
        # Clean up the path in case there's any extra text
        audio_path = str(audio_path).strip()
        print(f"✓ Audio generated: {audio_path}\n")
        
        print(f"{'='*60}")
        print("Workflow completed successfully!")
        print(f"{'='*60}\n")
        
        return summary, audio_path
