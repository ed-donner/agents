"""
Researcher Node - Researches the topic using Wikipedia and web search.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from state import State
from tools import get_wikipedia_tool, get_search_tool


class ResearchOutput(BaseModel):
    """Structured output from the Researcher node."""
    prerequisites: List[str] = Field(description="List of prerequisite topics/skills needed")
    key_concepts: List[str] = Field(description="List of key concepts to learn")
    research_summary: str = Field(description="Summary of findings about the topic")


class ResearcherNode:
    """
    Research the topic using Wikipedia and web search.
    Extracts prerequisites, key concepts, and creates a summary.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.wiki_tool = get_wikipedia_tool()
        self.search_tool = get_search_tool()
        self.llm = ChatOpenAI(model=model)
        self.llm_with_output = self.llm.with_structured_output(ResearchOutput)
        self.system_prompt = """You are a learning path researcher. Analyze the provided information 
and extract key details about the topic to help create a learning curriculum.
Consider the user's current skill level when identifying prerequisites."""

    def execute(self, state: State) -> Dict[str, Any]:
        """Execute the researcher node."""
        topic = state["topic"]
        skill_level = state["current_skill_level"]
        wiki_result = self.wiki_tool.invoke(topic)
        search_results = self.search_tool.invoke(f"{topic} learning roadmap prerequisites")
        search_text = ""
        if isinstance(search_results, list):
            for r in search_results[:3]:
                search_text += f"- {r.get('title', '')}: {r.get('content', '')}\n"
        
        user_prompt = f"""Topic: {topic}
User's current skill level: {skill_level}

Wikipedia information:
{wiki_result[:3000]}

Web search results:
{search_text[:2000]}

Based on this information, identify:
1. Prerequisites - what should someone know before learning {topic}?
2. Key concepts - what are the main topics/concepts within {topic}?
3. Research summary - a brief overview of what {topic} is and why it's valuable to learn."""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]
        result = self.llm_with_output.invoke(messages)
        return {
            "prerequisites": result.prerequisites,
            "key_concepts": result.key_concepts,
            "research_summary": result.research_summary,
            "messages": [{"role": "assistant", "content": f"Research complete for {topic}. Found {len(result.prerequisites)} prerequisites and {len(result.key_concepts)} key concepts."}]
        }
