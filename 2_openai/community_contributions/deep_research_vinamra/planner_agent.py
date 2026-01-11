from pydantic import BaseModel, Field
from agents import Agent
from guardrails import validate_research_input
from model_config import mimo_model

# Configuration
HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are an expert research strategist. Your task is to analyze a research query 
and create a comprehensive search plan.

Given a query, generate {HOW_MANY_SEARCHES} distinct web searches that will cover different aspects 
and perspectives of the topic.

**Guidelines:**
1. Ensure searches cover breadth (different aspects) and depth (specific details)
2. Include searches for recent developments, historical context, and expert opinions
3. Consider primary sources, academic research, and practical applications
4. Avoid redundant searches - each should target unique information
5. Make search terms specific enough to get quality results

**Output Format:**
Return a JSON object with this exact structure:
{{
  "searches": [
    {{
      "reason": "explanation of why this search is important",
      "query": "the search term to use"
    }},
    ...exactly {HOW_MANY_SEARCHES} items...
  ]
}}

**Example:**
Query: "Impact of AI on healthcare"
Output:
{{
  "searches": [
    {{
      "reason": "Recent effectiveness research on AI diagnostic capabilities",
      "query": "AI diagnostic tools accuracy studies 2024"
    }},
    {{
      "reason": "Understanding practical implementation barriers in healthcare settings",
      "query": "Healthcare AI implementation challenges hospitals"
    }},
    {{
      "reason": "Ethical considerations around patient privacy and AI medical decisions",
      "query": "AI medical ethics patient privacy concerns"
    }},
    {{
      "reason": "Specific application in radiology and medical imaging",
      "query": "Machine learning radiology imaging detection"
    }},
    {{
      "reason": "Economic impact analysis with real-world cost reduction data",
      "query": "AI healthcare cost reduction case studies"
    }}
  ]
}}
"""


class WebSearchItem(BaseModel):
    """Single web search item with reasoning"""
    reason: str = Field(
        description="Clear explanation of why this search is important and what unique information it will provide"
    )
    query: str = Field(
        description="Specific, well-crafted search term optimized for web search engines"
    )


class WebSearchPlan(BaseModel):
    """Complete search plan for research query"""
    searches: list[WebSearchItem] = Field(
        description=f"Exactly {HOW_MANY_SEARCHES} strategic web searches to comprehensively answer the query"
    )


planner_agent = Agent(
    name="PlannerAgent",
    instructions=INSTRUCTIONS,
    model=mimo_model,
    output_type=WebSearchPlan,
    input_guardrails=[validate_research_input],
)