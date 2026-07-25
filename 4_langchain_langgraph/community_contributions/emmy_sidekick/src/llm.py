"""LLM initialization and configuration"""

from langchain_groq import ChatGroq
from src.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from src.models import PlannerOutput


# Base LLM
llm = ChatGroq(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    groq_api_key=GROQ_API_KEY
)

# Planner LLM with structured output
planner_llm = llm.with_structured_output(PlannerOutput)

