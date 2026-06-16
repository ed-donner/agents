"""
Clinical Analyst Agent
Responsibility: Parse raw patient intake data and extract structured clinical facts.
"""

from src.utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a senior clinical data analyst at a hospital.
Your job is to read raw, unstructured patient notes and extract a clean, 
structured JSON summary of all medically relevant facts.

Output ONLY valid JSON — no prose, no markdown fences. Structure:
{
  "patient_id": "",
  "patient_name": "",
  "age": 0,
  "gender": "",
  "admission_date": "",
  "discharge_date": "",
  "primary_diagnosis": "",
  "secondary_diagnoses": [],
  "chief_complaint": "",
  "vital_signs": {
    "bp": "", "hr": "", "temp": "", "spo2": "", "rr": ""
  },
  "labs": [],
  "procedures": [],
  "medications_administered": [],
  "allergies": [],
  "attending_physician": "",
  "ward": ""
}

Extract only what is explicitly stated. Use null for missing fields.
"""


def run(patient_data: str) -> str:
    """
    Extract structured clinical facts from raw patient notes.
    Returns a JSON string.
    """
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Extract structured data from the following patient notes:\n\n{patient_data}",
        temperature=0.1,  # low temp for factual extraction
    )
