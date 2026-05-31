from pydantic import BaseModel, Field
from agents import Agent

INSTRUCTIONS = """You are a clinical query parser specialized in oncology and pharmacogenomics.
Given a clinical query, extract the following structured information:
- Disease type (e.g., "Non-Small Cell Lung Cancer", "NSCLC")
- Gene(s) involved (e.g., "EGFR", "KRAS")
- Specific mutation(s) (e.g., "T790M", "L858R", "exon 19 deletion")
- Additional clinical context (patient characteristics, treatment history, etc.)

Be precise and use standard nomenclature. If information is not explicitly stated, mark it as None.
"""


class ClinicalQuery(BaseModel):
    """Structured representation of a clinical pharmacogenomic query"""
    
    disease: str = Field(description="The disease or cancer type (e.g., 'Non-Small Cell Lung Cancer', 'NSCLC')")
    genes: list[str] = Field(description="List of genes mentioned (e.g., ['EGFR', 'ALK'])")
    mutations: list[str] = Field(description="Specific mutations mentioned (e.g., ['T790M', 'L858R'])")
    clinical_context: str = Field(description="Additional clinical context such as treatment history, patient characteristics, or specific questions")
    search_focus: str = Field(description="The primary research focus: therapies, resistance mechanisms, clinical trials, prognosis, etc.")


query_parser_agent = Agent(
    name="QueryParserAgent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ClinicalQuery,
)

