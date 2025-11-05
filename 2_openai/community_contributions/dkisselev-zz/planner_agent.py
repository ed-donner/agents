from pydantic import BaseModel, Field
from agents import Agent

HOW_MANY_SEARCHES = 6  #  multipple of 3

INSTRUCTIONS = f"""You are a medical research planning specialist in oncology and pharmacogenomics.

Given a parsed clinical query with disease, genes, mutations, and research focus, create a comprehensive 
search plan across three specialized databases:

1. **PubMed**: For peer-reviewed biomedical literature
2. **ClinicalTrials.gov**: For ongoing and completed clinical trials
3. **PharmGKB**: For pharmacogenomic drug-gene interactions

You must generate EXACTLY {HOW_MANY_SEARCHES} searches distributed as:
- {HOW_MANY_SEARCHES//3} PubMed searches (different angles: treatment/mechanisms, outcomes/resistance, etc.)
- {HOW_MANY_SEARCHES//3} ClinicalTrials.gov searches (different phases or interventions)
- {HOW_MANY_SEARCHES//3} PharmGKB searches (gene-drug interactions, often with different drug classes)

For each search:
- Use appropriate medical terminology and gene nomenclature
- Be specific (include mutation details when relevant)
- Tailor queries to each database's strengths
- Focus on clinically actionable information

Example for "NSCLC with EGFR T790M mutation":
- PubMed: "NSCLC EGFR T790M osimertinib resistance mechanisms"
- PubMed: "EGFR T790M mutation treatment outcomes survival"
- ClinicalTrials: "NSCLC EGFR T790M"
- ClinicalTrials: "non-small cell lung cancer third generation EGFR inhibitor"
- PharmGKB: "EGFR osimertinib"
- PharmGKB: "EGFR erlotinib gefitinib"
"""

class MedicalSearchItem(BaseModel):
    database: str = Field(description="Database to search: 'PubMed', 'ClinicalTrials', or 'PharmGKB'")
    reason: str = Field(description="Why this search is important for answering the clinical query")
    query: str = Field(description="The optimized search query for this specific database")


class MedicalSearchPlan(BaseModel):
    searches: list[MedicalSearchItem] = Field(
        description=f"List of {HOW_MANY_SEARCHES} medical database searches ({HOW_MANY_SEARCHES//3} PubMed, {HOW_MANY_SEARCHES//3} ClinicalTrials, {HOW_MANY_SEARCHES//3} PharmGKB)"
    )
    

planner_agent = Agent(
    name="MedicalPlannerAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=MedicalSearchPlan,
)
