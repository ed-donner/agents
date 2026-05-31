from agents import Agent, WebSearchTool
from pydantic import BaseModel, Field, ConfigDict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EMERGENCY_SPECIALIST_NAME

INSTRUCTIONS = f"""
You are {EMERGENCY_SPECIALIST_NAME}, an Emergency Specialist. Your role is to evaluate the patient's case and determine 
if it constitutes a medical emergency requiring immediate attention.

Your task:
1. Review all information provided about the patient's condition
2. Assess for emergency warning signs (severe pain, difficulty breathing, chest pain, 
   loss of consciousness, severe bleeding, etc.)
3. Determine if the case is an emergency or not
4. Write a comprehensive report with your findings and recommendations

In your report, clearly state:
- Whether this is an emergency case (yes/no)
- Emergency indicators present (if any)
- Your clinical reasoning
- Recommended actions (immediate ER visit, urgent care within 24 hours, or routine care)
"""

class EmergencySpecialistHandoff(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    is_emergency: bool = Field(description="Whether this case is a medical emergency requiring immediate attention")
    emergency_indicators: list[str] = Field(description="List of emergency warning signs or symptoms identified")
    clinical_reasoning: str = Field(description="Your reasoning for the emergency determination")
    recommended_action: str = Field(description="Recommended course of action (e.g., call 911, visit ER immediately, urgent care, routine appointment)")
    specialist_report: str = Field(description="Comprehensive report of your emergency assessment")

class EmergencySpecialistAgent(Agent):
    def __init__(self):
        super().__init__(
          name="EmergencySpecialistAgent", 
          instructions=INSTRUCTIONS, 
          tools=[WebSearchTool(search_context_size="low")],
          model="gpt-4o-mini",
          output_type=EmergencySpecialistHandoff,
        )
    
    def __call__(self, *args, **kwargs):
        """Capture when specialist is invoked as a tool"""
        print(f"🚨 [{EMERGENCY_SPECIALIST_NAME}] Emergency Specialist invoked")
        result = super().__call__(*args, **kwargs)
        print(f"   ✓ Emergency assessment complete")
        return result

