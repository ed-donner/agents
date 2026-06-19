"""Orchestrator for coordinating news summary workflow."""

import json
from typing import Tuple
from agents import Runner, ToolCallOutputItem
from news_agents import (
    news_aggregator_agent,
    summarizer_agent,
    audio_generator_agent,
)


class NewsSummaryOrchestrator:
    """Orchestrates the news summary workflow using multiple autonomous agents.
    
    Uses the OpenAI Agents SDK Runner to execute agents autonomously.
    Each agent decides when and how to use its tools based on instructions.
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
        print("Step 1: Fetching news articles...")
        aggregator_result = await Runner.run(
            self.aggregator,
            f"Fetch the latest news articles about {topic}"
        )
        
        # Extract articles from the tool call outputs
        articles = None
        for item in aggregator_result.new_items:
            if isinstance(item, ToolCallOutputItem):
                result = item.output
                if isinstance(result, dict) and "articles" in result:
                    articles = result["articles"]
                    break
        
        if not articles:
            raise ValueError("Failed to fetch articles from aggregator agent")
        
        print(f"✓ Fetched {len(articles)} articles\n")
        
        # Step 2: Ask the summarizer agent to create a summary
        print("Step 2: Creating summary...")
        summarizer_result = await Runner.run(
            self.summarizer,
            f"Summarize these news articles into a 300-word briefing: {json.dumps(articles)}"
        )
        
        summary = summarizer_result.final_output
        print(f"✓ Summary created ({len(summary.split())} words)\n")
        
        # Step 3: Ask the audio generator agent to create audio
        print("Step 3: Generating audio...")
        audio_result = await Runner.run(
            self.audio_generator,
            f"Convert this text to speech: {summary}"
        )
        
        # Extract audio path from the tool call outputs
        audio_path = None
        for item in audio_result.new_items:
            if isinstance(item, ToolCallOutputItem):
                result = item.output
                if isinstance(result, str) and (result.endswith('.mp3') or '/' in result):
                    audio_path = result.strip()
                    break
        
        if not audio_path:
            raise ValueError("Failed to generate audio from audio generator agent")
        
        print(f"✓ Audio generated: {audio_path}\n")
        
        print(f"{'='*60}")
        print("Workflow completed successfully!")
        print(f"{'='*60}\n")
        
        return summary, audio_path
