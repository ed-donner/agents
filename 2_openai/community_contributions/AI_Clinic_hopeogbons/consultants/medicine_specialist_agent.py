from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field, ConfigDict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MEDICINE_SPECIALIST_NAME

INSTRUCTIONS = f"""
You are {MEDICINE_SPECIALIST_NAME}, a Medicine Specialist. Your role is to evaluate the patient's case and determine 
if it requires medical treatment through medications, therapies, or other non-surgical 
interventions.

Your task:
1. Review all information provided about the patient's condition
2. Assess symptoms and medical history to identify potential diagnoses
3. Determine if medical treatment is appropriate for this case
4. Recommend specific medications, dosages, or treatment protocols if applicable
5. Write a comprehensive report with your findings and recommendations

In your report, clearly state:
- Whether this case requires medical treatment (yes/no)
- Potential diagnoses or conditions identified
- Your clinical reasoning and differential diagnosis
- Recommended medications or treatments (if applicable)
- Duration of treatment and follow-up recommendations
"""

class MedicineSpecialistHandoff(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    requires_medical_treatment: bool = Field(description="Whether this case requires medical treatment")
    potential_diagnoses: list[str] = Field(description="List of potential diagnoses or conditions identified")
    clinical_reasoning: str = Field(description="Your reasoning for the diagnosis and treatment recommendations")
    recommended_medications: list[str] = Field(description="Recommended medications or treatments with dosages (if applicable)")
    treatment_duration: str = Field(description="Expected duration of treatment and follow-up schedule")
    specialist_report: str = Field(description="Comprehensive report of your medical assessment")

class MedicineSpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
          name="MedicineSpecialistAgent", 
          instructions=INSTRUCTIONS, 
          tools=[WebSearchTool(search_context_size="low")],
          model="gpt-4o-mini",
          output_type=MedicineSpecialistHandoff,
        )
    
    def __call__(self, *args, **kwargs):
        """Capture when specialist is invoked as a tool"""
        print(f"💊 [{MEDICINE_SPECIALIST_NAME}] Medicine Specialist invoked")
        result = super().__call__(*args, **kwargs)
        print(f"   ✓ Medical evaluation complete")
        return result

