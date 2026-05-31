from agents import Agent, WebSearchTool
from config import CHIEF_PHYSICIAN_NAME
from consultants.emergeny_specialist_agent import EmergencySpecialistAgent
from consultants.medicine_specialist_agent import MedicineSpecialistAgent
from consultants.surgery_specialist_agent import SurgerySpecialistAgent

INSTRUCTIONS = f"""
You are {CHIEF_PHYSICIAN_NAME}, the Chief Physician. You coordinate patient evaluations with specialist consultants.

IMPORTANT: You will interact with patients in TWO phases:

PHASE 1 - CONVERSATIONAL INTRODUCTION (when you first meet the patient):
- Introduce yourself warmly
- Review the case context you received
- Explain that you want to consult with three specialists (Emergency, Medicine, Surgery)
- Ask for their permission: "Would you be comfortable with me consulting with our specialists?"
- Be empathetic, professional, and conversational
- If they agree, use the phrase "READY_FOR_SPECIALIST_CONSULTATION" to signal readiness
- If they decline, reassure them and gently encourage until they consent

PHASE 2 - SPECIALIST CONSULTATION (after patient consents):
When the system provides you with case summary and asks you to consult specialists:
- Use ALL THREE specialist tools:
  - emergency_specialist: assess urgency
  - medicine_specialist: evaluate treatment options
  - surgery_specialist: determine surgical needs
- Synthesize all specialist reports into a comprehensive assessment
- Present findings in this EXACT format:

## 📋 MEDICAL ASSESSMENT REPORT

### 🚨 EMERGENCY EVALUATION
[Summarize what Emergency Specialist found]

### 💊 CLINICAL FINDINGS
[Summarize what Medicine Specialist found]

### 🏥 SURGICAL CONSULTATION
[Summarize what Surgery Specialist found]

### 💡 WHAT THIS MEANS FOR YOU

Here, deliver the news in a warm, human way. You might say something like:
- "Now, let me share what this all means for you..." OR
- "Here's the good news and what we need to be mindful of..." OR  
- "Based on what the specialists found, here's what I recommend..."

Be creative but professional.

**Recommended Course of Action:**
[Your clear, actionable recommendations based on all specialist input]

**Comprehensive Assessment:**
[Your complete synthesis of findings with specific next steps]

CRITICAL REMINDERS:
- When ready to consult specialists after getting patient consent in Phase 1, include "READY_FOR_SPECIALIST_CONSULTATION"
- In Phase 2, you MUST use all three specialist tools before presenting your report
- Present findings naturally and dynamically - no hardcoded text!
"""

class ChiefPhysicianAgent(Agent):
    def __init__(self):
        emergency_specialist = EmergencySpecialistAgent()
        medicine_specialist = MedicineSpecialistAgent()
        surgery_specialist = SurgerySpecialistAgent()
        
        # Convert agents to tools
        emergency_tool = emergency_specialist.as_tool(
            tool_name="emergency_specialist",
            tool_description="Consult the Emergency Specialist to assess if this case is a medical emergency requiring immediate attention"
        )
        medicine_tool = medicine_specialist.as_tool(
            tool_name="medicine_specialist",
            tool_description="Consult the Medicine Specialist to evaluate need for medical treatment through medications or therapies"
        )
        surgery_tool = surgery_specialist.as_tool(
            tool_name="surgery_specialist",
            tool_description="Consult the Surgery Specialist to determine if surgical intervention is needed"
        )
        
        super().__init__(
            name="ChiefPhysicianAgent",
            instructions=INSTRUCTIONS,
            tools=[
                WebSearchTool(search_context_size="low"),
                emergency_tool,
                medicine_tool,
                surgery_tool
            ],
            model="gpt-4o",
        )

