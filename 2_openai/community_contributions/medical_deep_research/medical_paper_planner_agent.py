from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 5

INSTRUCTIONS = f"""You are a medical research assistant specialized in academic literature search planning. 
Given a medical or clinical query, create a comprehensive search plan for finding relevant academic papers, 
journal articles, and peer-reviewed research.

Your searches should:
- Use medical terminology, MeSH terms, and academic keywords
- Target specific aspects: mechanisms, clinical trials, epidemiology, treatment protocols, outcomes, etc.
- Consider different study types: RCTs, meta-analyses, systematic reviews, case studies
- Include synonyms and related medical terms
- Focus on peer-reviewed sources: PubMed, MEDLINE, clinical journals, medical databases

Output {HOW_MANY_SEARCHES} distinct search queries that will comprehensively cover the medical topic."""


class MedicalSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to comprehensively answer the medical query. Include what aspect of the topic this covers.")
    query: str = Field(description="The search query optimized for medical/academic databases (use MeSH terms, medical terminology, study types where appropriate).")


class MedicalSearchPlan(BaseModel):
    searches: list[MedicalSearchItem] = Field(description="A list of medical/academic searches to perform to comprehensively answer the query.")
    

medical_planner_agent = Agent(
    name="MedicalPlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=MedicalSearchPlan,
)

