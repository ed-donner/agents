"""
Medical Writer Agent
Responsibility: Compose a professional, formatted discharge summary document
combining clinical data and discharge plan into a readable clinical note.
"""

from src.utils.llm_client import call_llm

SYSTEM_PROMPT = """You are a board-certified medical writer specializing in 
clinical documentation for hospitals.

Given structured patient data and a discharge plan (both in JSON), write a 
complete, professional discharge summary in plain text.

Use this exact structure with these section headers:

DISCHARGE SUMMARY
=================

PATIENT INFORMATION
HOSPITAL COURSE
DIAGNOSES
PROCEDURES PERFORMED
RELEVANT INVESTIGATIONS
DISCHARGE MEDICATIONS
DISCHARGE PLAN
FOLLOW-UP INSTRUCTIONS
PATIENT EDUCATION
RETURN TO EMERGENCY DEPARTMENT IF

---
Attending Physician: [name]
Summary prepared by: MedScribe AI
Date: [discharge date]

Rules:
- Write in professional clinical language
- Be concise but complete — no padding
- Every section must be present
- Use plain text only, no markdown symbols
"""


def run(patient_json: str, plan_json: str) -> str:
    """
    Compose a complete discharge summary from patient data and discharge plan.
    Returns a plain-text clinical document.
    """
    prompt = (
        f"PATIENT DATA:\n{patient_json}\n\n"
        f"DISCHARGE PLAN:\n{plan_json}\n\n"
        "Write the complete discharge summary."
    )
    return call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=prompt,
        temperature=0.4,
    )
