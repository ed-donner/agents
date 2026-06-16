"""
Discharge Planner Agent
Responsibility: Generate a clinically sound discharge plan from structured patient data.
"""

from src.utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a senior hospital discharge planning specialist.
Given a structured JSON summary of a patient's hospital stay, produce a 
comprehensive discharge plan.

Your output must be a JSON object with exactly this structure:
{
  "discharge_condition": "Stable | Improved | Critical",
  "follow_up_appointments": [
    {"specialist": "", "timeframe": "", "reason": ""}
  ],
  "discharge_medications": [
    {"name": "", "dose": "", "frequency": "", "duration": "", "instructions": ""}
  ],
  "activity_restrictions": [],
  "diet_instructions": "",
  "wound_care": "",
  "warning_signs": [],
  "patient_education_points": [],
  "return_to_er_criteria": []
}

Base every recommendation strictly on the provided clinical data.
Output ONLY valid JSON — no prose, no markdown fences.
"""


def run(structured_patient_json: str) -> str:
    """
    Produce a discharge plan from structured patient data JSON.
    Returns a JSON string.
    """
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Generate a discharge plan for this patient:\n\n{structured_patient_json}",
        temperature=0.2,
    )
