from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field, ConfigDict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import SURGERY_SPECIALIST_NAME

INSTRUCTIONS = f"""
You are {SURGERY_SPECIALIST_NAME}, a Surgery Specialist. Your role is to evaluate the patient's case and determine 
if it requires surgical intervention.

Your task:
1. Review all information provided about the patient's condition
2. Assess symptoms and medical history to identify conditions that may require surgery
3. Determine if surgical intervention is necessary, recommended, or optional
4. Evaluate urgency level (emergency, urgent, elective)
5. Write a comprehensive report with your findings and recommendations

In your report, clearly state:
- Whether this case requires surgery (yes/no/maybe)
- Type of surgical procedure recommended (if applicable)
- Your clinical reasoning for surgical vs non-surgical management
- Urgency level (emergency, urgent within days/weeks, elective, or can wait)
- Potential risks and benefits of surgery
- Pre-operative requirements and post-operative care expectations
"""

class SurgerySpecialistHandoff(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    requires_surgery: str = Field(description="Whether surgery is required: 'yes', 'no', or 'maybe' (needs further evaluation)")
    surgical_procedure: str = Field(description="Type of surgical procedure recommended (if applicable)")
    clinical_reasoning: str = Field(description="Your reasoning for surgical vs non-surgical management")
    urgency_level: str = Field(description="Urgency: emergency, urgent, elective, or observation")
    risks_and_benefits: str = Field(description="Summary of potential risks and benefits of surgery")
    pre_post_operative_notes: str = Field(description="Pre-operative requirements and post-operative care expectations")
    specialist_report: str = Field(description="Comprehensive report of your surgical assessment")

class SurgerySpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
          name="SurgerySpecialistAgent", 
          instructions=INSTRUCTIONS, 
          tools=[WebSearchTool(search_context_size="low")],
          model="gpt-4o-mini",
          output_type=SurgerySpecialistHandoff,
        )
    
    def __call__(self, *args, **kwargs):
        """Capture when specialist is invoked as a tool"""
        print(f"🏥 [{SURGERY_SPECIALIST_NAME}] Surgery Specialist invoked")
        result = super().__call__(*args, **kwargs)
        print(f"   ✓ Surgery assessment complete")
        return result

